"""Run one VentureLens agent at a time. Each agent reads the saved output of the
agents before it and saves its own output as JSON in data/output/<run_id>/.

  python run_agent.py extraction
  python run_agent.py gatekeeper
  python run_agent.py market
  python run_agent.py financial
  python run_agent.py traction
  python run_agent.py judge
  python run_agent.py memo          (accepted)   or   python run_agent.py diagnostic (rejected)
  python run_agent.py status

Every command except extraction uses the latest run, or pass --run <run_id>.
"""
import argparse
import asyncio
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from google.genai import types

import pipeline as p
from knowledge import find_passages

# ---- Input and output locations (edit these) ----
PITCH_DECK_PATH = "sample_data/strong_pitch_deck.pdf"   # input 1
GST_DOC_PATH = "sample_data/strong_gst_document.pdf"    # input 2
OUTPUT_DIR = Path("data/output")                        # every agent's JSON output is saved here


def all_runs():
    if not OUTPUT_DIR.exists():
        return []
    return sorted((d for d in OUTPUT_DIR.iterdir() if d.is_dir()), key=lambda d: d.name)


def get_run(args):
    if args.run:
        run = OUTPUT_DIR / args.run
        if not run.is_dir():
            sys.exit(f"No run called {args.run}. Use 'status' to list runs.")
        return run
    runs = all_runs()
    if not runs:
        sys.exit("No runs yet. Start with: python run_agent.py extraction")
    return runs[-1]


def load(run, name):
    path = run / name
    if not path.exists():
        sys.exit(f"Missing {name} in {run.name}. Run the earlier agent first.")
    return json.loads(path.read_text(encoding="utf-8"))


def save(run, name, data):
    (run / name).write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(json.dumps(data, indent=2))
    print(f"\nSaved {run / name}")


def require_gate_passed(run):
    gate = load(run, "02_gate.json")
    if gate.get("gate_status") != "PASSED":
        sys.exit("The gatekeeper did not pass this application, so there is nothing to score. "
                 "Run: python run_agent.py diagnostic")
    return gate


SCORER_FILES = {
    "market": "03_market_tam.json",
    "financial": "04_financial.json",
    "traction": "05_traction.json",
}


def load_scorers(run):
    return [load(run, f) for f in SCORER_FILES.values()]


def scorer_details(scorers):
    return [{"agent": s["agent"], "findings": s.get("findings", {}),
             "reasoning_summary": s.get("reasoning_summary", "")} for s in scorers]


async def cmd_extraction(args):
    pitch, gst = Path(args.pitch), Path(args.gst)
    for f in (pitch, gst):
        if not f.exists():
            sys.exit(f"File not found: {f}")
    run = OUTPUT_DIR / datetime.now().strftime("%Y%m%d_%H%M%S")
    run.mkdir(parents=True)
    shutil.copy(pitch, run / "pitch_deck.pdf")
    shutil.copy(gst, run / "gst_document.pdf")
    extracted = await p.call_agent(p.extraction_agent, [
        types.Part.from_bytes(data=pitch.read_bytes(), mime_type="application/pdf"),
        types.Part.from_bytes(data=gst.read_bytes(), mime_type="application/pdf"),
        types.Part(text="Extract the data from this pitch deck and GST document."),
    ])
    save(run, "01_extraction.json", extracted)
    print(f"Run id: {run.name}\nNext: python run_agent.py gatekeeper")


async def cmd_gatekeeper(args):
    run = get_run(args)
    gate = await p.call_agent(p.gatekeeper_agent, [p.text_part(load(run, "01_extraction.json"))])
    save(run, "02_gate.json", gate)
    if gate.get("gate_status") == "PASSED":
        print("Next: python run_agent.py market   (then financial, traction)")
    else:
        print("Mandate failed. Next: python run_agent.py diagnostic")


def scorer_command(key, agent):
    async def run_it(args):
        run = get_run(args)
        require_gate_passed(run)
        extracted = load(run, "01_extraction.json")
        result = await p.median_run(agent, [p.text_part(extracted)], p.call_agent, runs=args.runs)
        save(run, SCORER_FILES[key], result)
    return run_it


async def cmd_judge(args):
    run = get_run(args)
    require_gate_passed(run)
    scorers = load_scorers(run)
    total = sum(int(s["score"]) for s in scorers)
    decision = "ACCEPTED" if total >= args.cutoff else "REJECTED"
    judge_said = await p.call_agent(p.judge_agent, [p.text_part({
        "cutoff": args.cutoff,
        "scorer_outputs": [{"agent": s["agent"], "score": s["score"], "max_score": s["max_score"]}
                           for s in scorers],
    })])
    if judge_said.get("final_score") != total or judge_said.get("decision") != decision:
        print(f"WARNING: judge said {judge_said.get('final_score')} / {judge_said.get('decision')}, "
              f"real total is {total} / {decision}. Using the real numbers.")
    judge = {"final_score": total, "cutoff": args.cutoff,
             "sub_scores": {s["agent"]: int(s["score"]) for s in scorers},
             "decision": decision}
    save(run, "06_judge.json", judge)
    print("Next: python run_agent.py " + ("memo" if decision == "ACCEPTED" else "diagnostic"))


async def cmd_memo(args):
    run = get_run(args)
    require_gate_passed(run)
    extracted = load(run, "01_extraction.json")
    scorers = load_scorers(run)
    judge = load(run, "06_judge.json")
    if judge["decision"] != "ACCEPTED":
        print("Note: this application was not accepted. The memo is normally only made for accepted ones.")
    memo = await p.call_agent(p.memo_agent, [p.text_part({
        "founder_info": extracted.get("founder_info", {}),
        "pitch_summary": extracted.get("pitch_content", {}).get("solution", ""),
        "final_score": judge["final_score"], "cutoff": judge["cutoff"],
        "sub_scores": judge["sub_scores"], "scorer_details": scorer_details(scorers),
    })])
    save(run, "07_memo.json", memo)


async def cmd_diagnostic(args):
    run = get_run(args)
    gate = load(run, "02_gate.json")
    if gate.get("gate_status") != "PASSED":
        payload = {"report_type": "MANDATE_FAILURE",
                   "failed_criteria": gate.get("failed_criteria", [])}
    else:
        scorers = load_scorers(run)
        judge = load(run, "06_judge.json")
        if judge["decision"] == "ACCEPTED":
            print("Note: this application was accepted. The diagnostic is normally only made for rejected ones.")
        payload = {"report_type": "SCORE_BELOW_CUTOFF",
                   "final_score": judge["final_score"], "cutoff": judge["cutoff"],
                   "sub_scores": judge["sub_scores"], "scorer_details": scorer_details(scorers)}
    payload["reference_passages"] = await find_passages(payload.get("scorer_details") or payload.get("failed_criteria", []))
    report = await p.call_agent(p.diagnostic_agent, [p.text_part(payload)])
    save(run, "07_report.json", report)


def cmd_status(args):
    runs = all_runs()
    if not runs:
        print("No runs yet.")
    for run in runs:
        print(run.name, "->", ", ".join(sorted(f.name for f in run.glob("*.json"))))


def main():
    parser = argparse.ArgumentParser(description="Run one VentureLens agent at a time.")
    sub = parser.add_subparsers(dest="command", required=True)

    def add(name):
        sp = sub.add_parser(name)
        sp.add_argument("--run", help="run id (default: the latest run)")
        return sp

    sp = add("extraction")
    sp.add_argument("--pitch", default=PITCH_DECK_PATH)
    sp.add_argument("--gst", default=GST_DOC_PATH)
    add("gatekeeper")
    for key in SCORER_FILES:
        sp = add(key)
        sp.add_argument("--runs", type=int, default=p.RUNS, help="scoring runs, median is kept (default 3)")
    sp = add("judge")
    sp.add_argument("--cutoff", type=int, default=p.CUTOFF)
    add("memo")
    add("diagnostic")
    add("status")

    args = parser.parse_args()
    handlers = {
        "extraction": cmd_extraction, "gatekeeper": cmd_gatekeeper,
        "market": scorer_command("market", p.market_tam_agent),
        "financial": scorer_command("financial", p.financial_agent),
        "traction": scorer_command("traction", p.traction_agent),
        "judge": cmd_judge, "memo": cmd_memo, "diagnostic": cmd_diagnostic,
    }
    if args.command == "status":
        cmd_status(args)
    else:
        asyncio.run(handlers[args.command](args))


if __name__ == "__main__":
    main()
