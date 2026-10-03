"""Google Cloud persistence for VentureLens.

Cloud Storage  -> the uploaded PDFs
Firestore      -> the full pipeline result (one document per application)
BigQuery       -> one flat row per application, for analytics

Configure with environment variables (put them in .env):
  GOOGLE_CLOUD_PROJECT   your GCP project id
  GCS_BUCKET             bucket name for uploads
  BQ_DATASET             BigQuery dataset (default: venturelens)
"""
import os
from datetime import datetime, timezone

PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
BUCKET = os.getenv("GCS_BUCKET")
BQ_DATASET = os.getenv("BQ_DATASET", "venturelens")
BQ_TABLE = "applications"
COLLECTION = "applications"

BQ_SCHEMA = [
    ("application_id", "STRING"),
    ("created_at", "TIMESTAMP"),
    ("status", "STRING"),
    ("final_score", "INTEGER"),
    ("cutoff", "INTEGER"),
    ("market_score", "INTEGER"),
    ("financial_score", "INTEGER"),
    ("traction_score", "INTEGER"),
    ("elapsed_seconds", "FLOAT"),
]


def configured():
    return bool(PROJECT and BUCKET)


def _sub_score(sub_scores, keyword):
    for name, value in (sub_scores or {}).items():
        if keyword in name.lower():
            return int(value)
    return None


def _upload_files(application_id, pitch, gst):
    from google.cloud import storage

    bucket = storage.Client(project=PROJECT).bucket(BUCKET)
    base = f"applications/{application_id}"
    bucket.blob(f"{base}/pitch_deck.pdf").upload_from_string(pitch, content_type="application/pdf")
    bucket.blob(f"{base}/gst_document.pdf").upload_from_string(gst, content_type="application/pdf")
    return {"pitch_deck": f"gs://{BUCKET}/{base}/pitch_deck.pdf",
            "gst_document": f"gs://{BUCKET}/{base}/gst_document.pdf"}


def _save_firestore(application_id, record):
    from google.cloud import firestore

    firestore.Client(project=PROJECT).collection(COLLECTION).document(application_id).set(record)


def _ensure_table(client):
    from google.cloud import bigquery

    client.create_dataset(bigquery.Dataset(f"{PROJECT}.{BQ_DATASET}"), exists_ok=True)
    client.create_table(
        bigquery.Table(
            f"{PROJECT}.{BQ_DATASET}.{BQ_TABLE}",
            schema=[bigquery.SchemaField(n, t) for n, t in BQ_SCHEMA],
        ),
        exists_ok=True,
    )


def _save_bigquery(row):
    from google.cloud import bigquery

    client = bigquery.Client(project=PROJECT)
    _ensure_table(client)
    errors = client.insert_rows_json(f"{PROJECT}.{BQ_DATASET}.{BQ_TABLE}", [row])
    if errors:
        raise RuntimeError(f"BigQuery insert failed: {errors}")


def save_application(application_id, pitch, gst, result):
    """Store one evaluated application everywhere. Returns what succeeded."""
    if not configured():
        return {"stored": False, "reason": "GOOGLE_CLOUD_PROJECT / GCS_BUCKET not set"}

    now = datetime.now(timezone.utc)
    judge = result.get("judge") or {}
    sub = judge.get("sub_scores", {})
    outcome = {}

    try:
        files = _upload_files(application_id, pitch, gst)
        outcome["storage"] = "ok"
    except Exception as e:
        files, outcome["storage"] = {}, f"failed: {e}"

    try:
        _save_firestore(application_id, {
            "application_id": application_id,
            "created_at": now,
            "status": result["status"],
            "files": files,
            "result": result,
        })
        outcome["firestore"] = "ok"
    except Exception as e:
        outcome["firestore"] = f"failed: {e}"

    try:
        _save_bigquery({
            "application_id": application_id,
            "created_at": now.isoformat(),
            "status": result["status"],
            "final_score": judge.get("final_score"),
            "cutoff": judge.get("cutoff"),
            "market_score": _sub_score(sub, "market"),
            "financial_score": _sub_score(sub, "financial"),
            "traction_score": _sub_score(sub, "traction"),
            "elapsed_seconds": result.get("elapsed_seconds"),
        })
        outcome["bigquery"] = "ok"
    except Exception as e:
        outcome["bigquery"] = f"failed: {e}"

    return {"stored": True, **outcome}


def get_application(application_id):
    from google.cloud import firestore

    doc = firestore.Client(project=PROJECT).collection(COLLECTION).document(application_id).get()
    return doc.to_dict() if doc.exists else None
