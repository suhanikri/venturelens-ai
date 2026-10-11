"""Input guardrails for VentureLens. Same style as the smart-support-agent example:
each check returns {"ok": bool, "reason": str, ...}."""
import re

MAX_PDF_BYTES = 15 * 1024 * 1024
MIN_PDF_BYTES = 200
MIN_CONFIDENCE = 0.7
REQUIRED_SECTIONS = ("founder_info", "gst_details", "pitch_content")

INJECTION_PATTERNS = [re.compile(p, re.I) for p in (
    r"ignore (all |any |the )?(previous|prior|above) (instructions|prompts?)",
    r"disregard (all |any |the )?(previous|prior|above)",
    r"system prompt",
    r"developer mode",
    r"jailbreak",
    r"you are now",
    r"(give|assign|award) (this|the) (startup|application|company)?\s?(a )?(score|rating) of",
    r"(score|rate) (this|it) (as )?(100|perfect|maximum)",
    r"(accept|approve) this (application|startup)",
    r"override (the )?(score|cutoff|decision)",
)]


def _strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)


def find_injection(text):
    return [p.pattern for p in INJECTION_PATTERNS if p.search(text)]


def validate_upload(pitch_bytes, gst_bytes):
    """Cheap checks on the two uploaded files before any model sees them."""
    for label, data in (("Pitch deck", pitch_bytes), ("GST document", gst_bytes)):
        if not isinstance(data, (bytes, bytearray)):
            return {"ok": False, "reason": f"{label} is missing."}
        if len(data) < MIN_PDF_BYTES:
            return {"ok": False, "reason": f"{label} is empty or too small to be a real PDF."}
        if len(data) > MAX_PDF_BYTES:
            return {"ok": False, "reason": f"{label} is larger than 15 MB."}
        if not data.startswith(b"%PDF"):
            return {"ok": False, "reason": f"{label} is not a PDF file."}
    return {"ok": True, "reason": "Looks fine"}


def validate_email(email):
    """An empty email is allowed (it is optional)."""
    email = (email or "").strip()
    if not email:
        return {"ok": True, "reason": "No email given", "cleaned_text": ""}
    if len(email) > 254 or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return {"ok": False, "reason": "Email address is not valid."}
    return {"ok": True, "reason": "Looks fine", "cleaned_text": email}


def validate_extraction(extracted):
    """Checks the extraction agent's JSON.
    ok=False means unusable. needs_review=True means a person should look before a decision."""
    if not isinstance(extracted, dict):
        return {"ok": False, "needs_review": True, "flags": ["Extraction is not a JSON object."],
                "reason": "Extraction is not a JSON object."}
    missing = [s for s in REQUIRED_SECTIONS if not isinstance(extracted.get(s), dict)]
    if missing:
        msg = "Extraction is missing: " + ", ".join(missing)
        return {"ok": False, "needs_review": True, "flags": [msg], "reason": msg}

    flags = []
    hits = sorted({h for s in _strings(extracted) for h in find_injection(s)})
    if hits:
        flags.append("Pitch text contains instruction-like phrases: " + "; ".join(hits))
    try:
        confidence = float(extracted.get("extraction_confidence", 1.0))
    except (TypeError, ValueError):
        confidence = 0.0
    if confidence < MIN_CONFIDENCE:
        flags.append(f"Low extraction confidence ({confidence}).")
    return {"ok": True, "needs_review": bool(flags), "flags": flags,
            "reason": "Flagged for review" if flags else "Looks fine"}
