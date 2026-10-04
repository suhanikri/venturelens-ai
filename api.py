"""FastAPI backend for VentureLens.

Run locally:  uvicorn api:app --reload --port 8000
"""
import time
import uuid

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

import delivery
import gcp_services
from pipeline import CUTOFF, run_pipeline

MAX_BYTES = 15 * 1024 * 1024  # 15 MB per file

app = FastAPI(title="VentureLens API", version="0.3.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


@app.get("/health")
def health():
    return {"status": "ok", "cutoff": CUTOFF, "gcp_storage": gcp_services.configured()}


async def read_pdf(upload: UploadFile, label: str) -> bytes:
    data = await upload.read()
    if not data:
        raise HTTPException(400, f"{label} is empty.")
    if len(data) > MAX_BYTES:
        raise HTTPException(413, f"{label} is larger than 15 MB.")
    if not data.startswith(b"%PDF"):
        raise HTTPException(400, f"{label} must be a PDF file.")
    return data


@app.post("/evaluate")
async def evaluate(
    pitch_deck: UploadFile = File(...),
    gst_document: UploadFile = File(...),
    founder_email: str = Form(""),
    cutoff: int = CUTOFF,
):
    """Run the pipeline, save to GCP, then deliver to Google Drive and Gmail."""
    pitch = await read_pdf(pitch_deck, "Pitch deck")
    gst = await read_pdf(gst_document, "GST document")

    started = time.time()
    try:
        result = await run_pipeline(pitch, gst, cutoff=cutoff)
    except RuntimeError as e:  # e.g. quota reached
        raise HTTPException(429, str(e))
    except Exception as e:
        raise HTTPException(500, f"Pipeline failed: {e}")

    result["elapsed_seconds"] = round(time.time() - started, 1)
    result["application_id"] = uuid.uuid4().hex[:12]
    # A storage or delivery problem must never lose the founder's result.
    result["storage"] = gcp_services.save_application(
        result["application_id"], pitch, gst, result
    )
    try:
        result["workspace"] = delivery.deliver(result, pitch, gst, founder_email)
    except Exception as e:
        result["workspace"] = {"enabled": True, "error": str(e)}
    return result


@app.get("/applications/{application_id}")
def get_application(application_id: str):
    if not gcp_services.configured():
        raise HTTPException(503, "GCP storage is not configured.")
    record = gcp_services.get_application(application_id)
    if not record:
        raise HTTPException(404, "Application not found.")
    return record
