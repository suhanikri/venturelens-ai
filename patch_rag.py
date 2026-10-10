from pathlib import Path


def patch(path, old, new):
    p = Path(path)
    t = p.read_text(encoding="utf-8")
    if new in t:
        print("already patched:", path)
        return
    if t.count(old) != 1:
        raise SystemExit(f"Could not patch {path}: expected 1 match, found {t.count(old)} for: {old}")
    p.write_text(t.replace(old, new), encoding="utf-8")
    print("patched:", path)


patch("pipeline.py", "from agents.memo_agent import memo_agent",
      "from agents.memo_agent import memo_agent\nfrom knowledge import find_passages")
patch("pipeline.py", '"failed_criteria": gate.get("failed_criteria", []),',
      '"failed_criteria": gate.get("failed_criteria", []),\n            "reference_passages": await find_passages(gate.get("failed_criteria", [])),')
patch("pipeline.py", '"report_type": "SCORE_BELOW_CUTOFF",',
      '"report_type": "SCORE_BELOW_CUTOFF",\n        "reference_passages": await find_passages(scorer_details),')
patch("run_agent.py", "import pipeline as p",
      "import pipeline as p\nfrom knowledge import find_passages")
patch("run_agent.py", "report = await p.call_agent(p.diagnostic_agent, [p.text_part(payload)])",
      'payload["reference_passages"] = await find_passages(payload.get("scorer_details") or payload.get("failed_criteria", []))\n    report = await p.call_agent(p.diagnostic_agent, [p.text_part(payload)])')
patch("pdf_reports.py", 'pdf.bullets(report.get("improvement_steps"))',
      'pdf.bullets(report.get("improvement_steps"))\n    if report.get("sources"):\n        pdf.heading("Sources")\n        pdf.bullets(report.get("sources"))')
