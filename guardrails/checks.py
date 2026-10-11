"""Applies the guardrails to a finished pipeline result."""
from guardrails.input_guardrails import validate_extraction, validate_upload
from guardrails.output_guardrails import review_flags, validate_memo, validate_report, validate_scorer
from knowledge import RETRIEVED


class GuardrailError(Exception):
    """The pipeline produced something unusable. Nothing is saved or sent."""


def check_upload(pitch, gst):
    r = validate_upload(pitch, gst)
    if not r["ok"]:
        raise GuardrailError(r["reason"])


def apply_guardrails(result):
    reasons = []
    ext = validate_extraction(result.get("extracted"))
    if ext["ok"]:
        reasons += ext["flags"]
    elif result.get("status") == "REJECTED_MANDATE":
        reasons += ext["flags"]   # keep the founder's diagnostic, but flag it
    else:
        raise GuardrailError(ext["reason"])

    for s in result.get("scorers", []):
        v = validate_scorer(s)
        if not v["ok"]:
            raise GuardrailError(v["reason"])

    if "report" in result:
        v = validate_report(result["report"], allowed_sources=RETRIEVED.get())
        if not v["ok"]:
            raise GuardrailError(v["reason"])
        result["report"] = v["cleaned_report"]

    if "memo" in result:
        v = validate_memo(result["memo"])
        if not v["ok"]:
            raise GuardrailError(v["reason"])

    judge = result.get("judge")
    if judge:
        reasons += review_flags(judge["final_score"], judge["cutoff"])

    result["review"] = {"needed": bool(reasons), "reasons": reasons}
    return result
