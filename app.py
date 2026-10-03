"""Streamlit frontend for VentureLens.

Run:  streamlit run app.py
Set API_URL to point at the backend (default http://localhost:8000).
"""
import json
import os

import requests
import streamlit as st

from pdf_reports import diagnostic_pdf, memo_pdf

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="VentureLens", layout="centered")


def pretty(key):
    return str(key).replace("_", " ").capitalize()


def render(value, level=0):
    """Show any JSON structure from the memo or report agents as readable text."""
    if isinstance(value, dict):
        for k, v in value.items():
            if isinstance(v, (dict, list)):
                st.markdown(f"{'#' * min(3 + level, 5)} {pretty(k)}")
                render(v, level + 1)
            else:
                st.markdown(f"**{pretty(k)}:** {v}")
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, (dict, list)):
                render(item, level + 1)
                st.divider()
            else:
                st.markdown(f"- {item}")
    else:
        st.write(value)


def show_scores(result):
    judge = result.get("judge")
    if not judge:
        return
    c1, c2, c3 = st.columns(3)
    c1.metric("Total score", judge["final_score"])
    c2.metric("Cutoff", judge["cutoff"])
    c3.metric("Decision", judge["decision"].capitalize())
    st.bar_chart(judge["sub_scores"])


st.title("VentureLens")
st.caption("Upload a pitch deck and GST document to screen an application.")

pitch = st.file_uploader("Pitch deck (PDF)", type="pdf")
gst = st.file_uploader("GST document (PDF)", type="pdf")

if st.button("Evaluate application", type="primary", disabled=not (pitch and gst)):
    with st.spinner("Agents are reviewing the application. This can take a few minutes."):
        try:
            resp = requests.post(
                f"{API_URL}/evaluate",
                files={
                    "pitch_deck": (pitch.name, pitch.getvalue(), "application/pdf"),
                    "gst_document": (gst.name, gst.getvalue(), "application/pdf"),
                },
                timeout=600,
            )
        except requests.exceptions.ConnectionError:
            st.error(f"Cannot reach the API at {API_URL}. Start it with: uvicorn api:app --port 8000")
            st.stop()
    if resp.status_code != 200:
        st.error(resp.json().get("detail", resp.text))
        st.stop()
    st.session_state["result"] = resp.json()

result = st.session_state.get("result")
if result:
    status = result["status"]
    st.caption(f"Completed in {result.get('elapsed_seconds', '?')} seconds")

    if status == "ACCEPTED":
        st.success("Accepted. Committee memo ready.")
        show_scores(result)
        st.header("Due diligence memo")
        render(result["memo"])
    elif status == "REJECTED_SCORE":
        st.warning("Not selected. Score is below the cutoff.")
        show_scores(result)
        st.header("Founder diagnostic report")
        render(result["report"])
    else:
        st.error("Not selected. Mandatory requirements were not met.")
        failed = result.get("gate", {}).get("failed_criteria", [])
        if failed:
            st.subheader("Failed requirements")
            render(failed)
        st.header("Founder diagnostic report")
        render(result["report"])

    if status == "ACCEPTED":
        st.download_button("Download memo (PDF)", memo_pdf(result), file_name="committee_memo.pdf", mime="application/pdf")
    else:
        st.download_button("Download diagnostic report (PDF)", diagnostic_pdf(result), file_name="founder_diagnostic.pdf", mime="application/pdf")
    with st.expander("Raw pipeline output"):
        st.json(result)
    st.download_button(
        "Download result (JSON)",
        json.dumps(result, indent=2),
        file_name="venturelens_result.json",
        mime="application/json",
    )

