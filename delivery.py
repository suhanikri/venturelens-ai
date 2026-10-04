"""Sends each application's outputs to Google Drive and Gmail."""
import json
import os
import re

import google_workspace as gw
from pdf_reports import diagnostic_pdf, memo_pdf, startup_name

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def deliver(result, pitch, gst, founder_email=""):
    if not gw.configured():
        return {"enabled": False, "reason": "Google sign-in token not configured"}

    accepted = result["status"] == "ACCEPTED"
    name = " ".join(str(startup_name(result)).split())
    app_id = result["application_id"]
    judge = result.get("judge") or {}
    if accepted:
        pdf_name, pdf = "committee_memo.pdf", memo_pdf(result)
    else:
        pdf_name, pdf = "founder_diagnostic.pdf", diagnostic_pdf(result)

    out = {"enabled": True}

    try:
        out["drive_folder"] = gw.save_to_drive(app_id, name, [
            ("pitch_deck.pdf", pitch, "application/pdf"),
            ("gst_document.pdf", gst, "application/pdf"),
            ("result.json", json.dumps(result, indent=2, default=str).encode(), "application/json"),
            (pdf_name, pdf, "application/pdf"),
        ])
    except Exception as e:
        out["drive"] = f"failed: {e}"

    try:
        if accepted:
            to = os.getenv("COMMITTEE_EMAIL", "").strip()
            subject = f"[VentureLens] Committee memo: {name}"
            body = (f"Attached is the due diligence memo for {name}.\n\n"
                    f"Score: {judge.get('final_score')} (cutoff {judge.get('cutoff')}).\n\n"
                    "VentureLens screening system")
        else:
            to = (founder_email or "").strip()
            subject = f"Your VentureLens application feedback: {name}"
            body = (f"Dear {name} team,\n\n"
                    "Thank you for applying. Your application was not selected for this round. "
                    "The attached report explains the reasons and gives concrete steps to improve.\n\n"
                    "Regards,\nVentureLens screening team")
        if not to:
            out["email"] = "skipped: no recipient address"
        elif not EMAIL_RE.match(to):
            out["email"] = "skipped: invalid email address"
        else:
            r = gw.send_report_email(to, subject, body, [(pdf_name, pdf)])
            out["email"] = f"{r['mode']} for {to}"
    except Exception as e:
        out["email"] = f"failed: {e}"

    return out
