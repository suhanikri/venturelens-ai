"""FastAPI backend for VentureLens.

Run locally:  uvicorn api:app --reload --port 8000
"""
import time
import uuid

from dotenv import load_dotenv

load_dotenv()

import collections
import hmac
import os

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware

import delivery
from guardrails.checks import GuardrailError
from guardrails.input_guardrails import validate_email
import gcp_services
from pipeline import CUTOFF, run_pipeline

MAX_BYTES = 15 * 1024 * 1024  # 15 MB per file

app = FastAPI(title="VentureLens API", version="0.3.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


API_KEY = os.getenv("VENTURELENS_API_KEY", "").strip()
if not API_KEY:
    raise RuntimeError("VENTURELENS_API_KEY is not set. Refusing to start.")
RATE_LIMIT = int(os.getenv("RATE_LIMIT_PER_HOUR", "20"))

def protect(request: Request, x_api_key: str = Header(default="")):
    """Requires the X-API-Key header (when a key is configured) and limits requests per client."""
    if not hmac.compare_digest(x_api_key.encode(), API_KEY.encode()):
        raise HTTPException(401, "Missing or invalid API key.")
    client = (request.headers.get("x-forwarded-for", "").split(",")[-1].strip()
              or (request.client.host if request.client else "unknown"))
    now = time.time()
    recent = [t for t in _hits[client] if now - t < 3600]
    if len(recent) >= RATE_LIMIT:
        raise HTTPException(429, f"Rate limit reached ({RATE_LIMIT} requests per hour).")
    recent.append(now)
    _hits[client] = recent


@app.get("/health")
def health():
    return {"status": "ok", "gcp_storage": gcp_services.configured(),
            "auth_required": bool(API_KEY)}


async def read_pdf(upload: UploadFile, label: str) -> bytes:
    data = await upload.read()
    if not data:
        raise HTTPException(400, f"{label} is empty.")
    if len(data) > MAX_BYTES:
        raise HTTPException(413, f"{label} is larger than 15 MB.")
    if not data.startswith(b"%PDF"):
        raise HTTPException(400, f"{label} must be a PDF file.")
    return data


@app.post("/evaluate", dependencies=[Depends(protect)])
async def evaluate(
    pitch_deck: UploadFile = File(...),
    gst_document: UploadFile = File(...),
    founder_email: str = Form(""),
):
    """Run the pipeline, save to GCP, then deliver to Google Drive and Gmail."""
    pitch = await read_pdf(pitch_deck, "Pitch deck")
    gst = await read_pdf(gst_document, "GST document")
    email_check = validate_email(founder_email)
    if not email_check["ok"]:
        raise HTTPException(400, email_check["reason"])
    founder_email = email_check["cleaned_text"]

    started = time.time()
    try:
                result = await run_pipeline(pitch, gst, cutoff=CUTOFF)
    except GuardrailError as e:
        raise HTTPException(422, str(e))
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


@app.get("/applications/{application_id}", dependencies=[Depends(protect)])
def get_application(application_id: str):
    if not gcp_services.configured():
        raise HTTPException(503, "GCP storage is not configured.")
    record = gcp_services.get_application(application_id)
    if not record:
        raise HTTPException(404, "Application not found.")
    return record

