"""Output guardrails for VentureLens: checks what the agents return before it is used."""
EXPECTED_MAX = {"market_tam": 30, "financial_cacltv": 40, "traction_moat": 30}
RISKY_PHRASES = ("ignore previous instructions", "i am the system", "15-digit")
MAX_REPORT_CHARS = 6000
BORDERLINE_MARGIN = 5


def _strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)


def _text_problem(obj):
    joined = " ".join(_strings(obj))
    if len(joined) > MAX_REPORT_CHARS:
        return f"Output is too long (max {MAX_REPORT_CHARS} characters)."
    lowered = joined.lower()
    found = [p for p in RISKY_PHRASES if p in lowered]
    if found:
        return "Output contains risky content: " + ", ".join(found)
    return None


def validate_scorer(result):
    """A scorer must return an integer score between 0 and its maximum, with the right maximum."""
    if not isinstance(result, dict):
        return {"ok": False, "reason": "Scorer output is not a JSON object."}
    agent = result.get("agent")
    if agent not in EXPECTED_MAX:
        return {"ok": False, "reason": f"Unknown scorer: {agent}"}
    try:
        score, maximum = int(result["score"]), int(result["max_score"])
    except (KeyError, TypeError, ValueError):
        return {"ok": False, "reason": f"{agent}: score or max_score is missing or not a number."}
    if maximum != EXPECTED_MAX[agent]:
        return {"ok": False, "reason": f"{agent}: max_score is {maximum}, expected {EXPECTED_MAX[agent]}."}
    if not 0 <= score <= maximum:
        return {"ok": False, "reason": f"{agent}: score {score} is outside 0 to {maximum}."}
    if not isinstance(result.get("findings", {}), dict):
        return {"ok": False, "reason": f"{agent}: findings is not an object."}
    return {"ok": True, "reason": "Looks fine"}


def validate_report(report, allowed_sources=()):
    """Founder diagnostic: required fields, risky text, and sources limited to retrieved documents."""
    if not isinstance(report, dict):
        return {"ok": False, "reason": "Report is not a JSON object."}
    if not isinstance(report.get("summary"), str) or not report["summary"].strip():
        return {"ok": False, "reason": "Report has no summary."}
    for key in ("rejection_drivers", "improvement_steps"):
        items = report.get(key)
        if not isinstance(items, list) or not items or not all(isinstance(i, str) and i.strip() for i in items):
            return {"ok": False, "reason": f"Report field '{key}' must be a non-empty list of text."}
    problem = _text_problem(report)
    if problem:
        return {"ok": False, "reason": problem}
    cleaned = dict(report)
    sources = report.get("sources") or []
    allowed = set(allowed_sources)
    kept = [s for s in sources if isinstance(s, str) and s in allowed]
    dropped = [s for s in sources if s not in kept]
    cleaned["sources"] = kept
    reason = "Looks fine"
    if dropped:
        reason = "Removed sources that were not retrieved: " + ", ".join(map(str, dropped))
    return {"ok": True, "reason": reason, "cleaned_report": cleaned}


def validate_memo(memo):
    if not isinstance(memo, dict):
        return {"ok": False, "reason": "Memo is not a JSON object."}
    if not isinstance(memo.get("one_pager_summary"), str) or not memo["one_pager_summary"].strip():
        return {"ok": False, "reason": "Memo has no summary."}
    for key in ("key_strengths", "operational_red_flags", "suggested_interview_questions"):
        if not isinstance(memo.get(key), list):
            return {"ok": False, "reason": f"Memo field '{key}' must be a list."}
    problem = _text_problem(memo)
    if problem:
        return {"ok": False, "reason": problem}
    return {"ok": True, "reason": "Looks fine"}


def review_flags(total, cutoff, confidence=1.0):
    """Reasons a person should look at an application before the result is acted on."""
    flags = []
    if abs(total - cutoff) <= BORDERLINE_MARGIN:
        flags.append(f"Score {total} is within {BORDERLINE_MARGIN} points of the cutoff {cutoff}.")
    try:
        if float(confidence) < 0.7:
            flags.append(f"Low extraction confidence ({confidence}).")
    except (TypeError, ValueError):
        flags.append("Extraction confidence is missing.")
    return flags
