import asyncio
import json
import re

from google.adk.runners import InMemoryRunner
from google.genai import types

from agents.extraction_agent import extraction_agent
from agents.gatekeeper_agent import gatekeeper_agent
from agents.market_tam_agent import market_tam_agent
from agents.financial_agent import financial_agent
from agents.traction_agent import traction_agent
from agents.judge_agent import judge_agent
from agents.diagnostic_agent import diagnostic_agent
from agents.memo_agent import memo_agent

CUTOFF = 60


def parse_json(text):
    text = text.strip()
    text = re.sub(r"^\x60{3}(?:json)?\s*", "", text)
    text = re.sub(r"\s*\x60{3}$", "", text)
    return json.loads(text)


def text_part(data):
    return types.Part(text=json.dumps(data))


async def call_agent(agent, parts, tries=4, wait_seconds=45):
    """Run one agent and return its JSON answer. Waits and retries on temporary errors."""
    for attempt in range(1, tries + 1):
        try:
            runner = InMemoryRunner(agent=agent, app_name="venturelens")
            session = await runner.session_service.create_session(
                app_name="venturelens", user_id="pipeline"
            )
            message = types.Content(role="user", parts=parts)
            text = ""
            async for event in runner.run_async(
                user_id="pipeline", session_id=session.id, new_message=message
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            text += part.text
            return parse_json(text)
        except Exception as e:
            error = str(e)
            if "PerDay" in error:
                raise RuntimeError(
                    "Daily free request limit reached. Try again after the reset."
                ) from e
            if attempt == tries:
                raise
            print(f"[{agent.name}] attempt {attempt} failed. Waiting {wait_seconds}s...")
            await asyncio.sleep(wait_seconds)


RUNS = 3


async def median_run(agent, parts, call, runs=RUNS):
    """Run a scorer several times and keep the run with the median score."""
    results = await asyncio.gather(*(call(agent, parts) for _ in range(runs)))
    ordered = sorted(results, key=lambda r: int(r["score"]))
    return ordered[len(ordered) // 2]

async def run_pipeline(pitch_bytes, gst_bytes, cutoff=CUTOFF, call=call_agent):
    # 1. Extraction
    extracted = await call(extraction_agent, [
        types.Part.from_bytes(data=pitch_bytes, mime_type="application/pdf"),
        types.Part.from_bytes(data=gst_bytes, mime_type="application/pdf"),
        types.Part(text="Extract the data from this pitch deck and GST document."),
    ])

    # 2. Gatekeeper: a failed mandate skips scoring entirely
    gate = await call(gatekeeper_agent, [text_part(extracted)])
    if gate.get("gate_status") != "PASSED":
        report = await call(diagnostic_agent, [text_part({
            "report_type": "MANDATE_FAILURE",
            "failed_criteria": gate.get("failed_criteria", []),
        })])
        return {"status": "REJECTED_MANDATE", "extracted": extracted,
                "gate": gate, "report": report}

    # 3. Three scorers run in parallel
    scorer_input = [text_part(extracted)]
    scorers = list(await asyncio.gather(
        median_run(market_tam_agent, scorer_input, call),
        median_run(financial_agent, scorer_input, call),
        median_run(traction_agent, scorer_input, call),
    ))

    # 4. Judge. Python does the maths too, and its numbers win if they disagree.
    total = sum(int(s["score"]) for s in scorers)
    decision = "ACCEPTED" if total >= cutoff else "REJECTED"
    sub_scores = {s["agent"]: int(s["score"]) for s in scorers}
    judge_said = await call(judge_agent, [text_part({
        "cutoff": cutoff,
        "scorer_outputs": [
            {"agent": s["agent"], "score": s["score"], "max_score": s["max_score"]}
            for s in scorers
        ],
    })])
    if judge_said.get("final_score") != total or judge_said.get("decision") != decision:
        print(f"WARNING: judge said {judge_said.get('final_score')} / "
              f"{judge_said.get('decision')}, real total is {total} / {decision}. "
              f"Using the real numbers.")
    judge = {"final_score": total, "cutoff": cutoff,
             "sub_scores": sub_scores, "decision": decision}

    scorer_details = [
        {"agent": s["agent"], "findings": s.get("findings", {}),
         "reasoning_summary": s.get("reasoning_summary", "")}
        for s in scorers
    ]

    # 5. Route to the right output agent
    if decision == "ACCEPTED":
        memo = await call(memo_agent, [text_part({
            "founder_info": extracted.get("founder_info", {}),
            "pitch_summary": extracted.get("pitch_content", {}).get("solution", ""),
            "final_score": total, "cutoff": cutoff, "sub_scores": sub_scores,
            "scorer_details": scorer_details,
        })])
        return {"status": "ACCEPTED", "extracted": extracted, "gate": gate,
                "scorers": scorers, "judge": judge, "memo": memo}

    report = await call(diagnostic_agent, [text_part({
        "report_type": "SCORE_BELOW_CUTOFF",
        "final_score": total, "cutoff": cutoff, "sub_scores": sub_scores,
        "scorer_details": scorer_details,
    })])
    return {"status": "REJECTED_SCORE", "extracted": extracted, "gate": gate,
            "scorers": scorers, "judge": judge, "report": report}

