import asyncio
from pipeline import run_pipeline


def score_obj(agent, score):
    return {"agent": agent, "score": score, "max_score": 30,
            "findings": {"flags": []}, "reasoning_summary": "fake"}


def make_fake(gate_pass=True, scores=(16, 27, 19), judge_lies=None):
    calls = []

    async def fake_call(agent, parts):
        name = agent.name
        calls.append(name)
        if name == "extraction_agent":
            return {"founder_info": {"startup_name": "FakeCo", "sector": "Test"},
                    "gst_details": {}, "pitch_content": {"solution": "A fake product"}}
        if name == "gatekeeper_agent":
            if gate_pass:
                return {"gate_status": "PASSED", "failed_criteria": []}
            return {"gate_status": "FAILED",
                    "failed_criteria": ["GST number is not disclosed"]}
        if name == "market_tam_agent":
            return score_obj("market_tam", scores[0])
        if name == "financial_agent":
            return score_obj("financial_cacltv", scores[1])
        if name == "traction_agent":
            return score_obj("traction_moat", scores[2])
        if name == "judge_agent":
            if judge_lies is not None:
                return judge_lies
            total = sum(scores)
            return {"final_score": total,
                    "decision": "ACCEPTED" if total >= 60 else "REJECTED"}
        if name == "memo_agent":
            return {"one_pager_summary": "fake memo"}
        if name == "diagnostic_agent":
            return {"summary": "fake report", "rejection_drivers": [],
                    "improvement_steps": []}
        raise ValueError(f"unexpected agent: {name}")

    return fake_call, calls


async def run_case(label, expect_status, must_call, must_not_call, **kwargs):
    fake, calls = make_fake(**kwargs)
    result = await run_pipeline(b"pdf", b"pdf", cutoff=60, call=fake)
    ok = (
        result["status"] == expect_status
        and all(c in calls for c in must_call)
        and all(c not in calls for c in must_not_call)
    )
    print("PASS" if ok else "FAIL", "-", label, "->", result["status"])
    if not ok:
        print("   agents called:", calls)
    return ok


async def main():
    scorers_and_judge = ["market_tam_agent", "financial_agent", "traction_agent", "judge_agent"]
    results = [
        await run_case("gate fails, scoring is skipped", "REJECTED_MANDATE",
                       ["diagnostic_agent"], scorers_and_judge + ["memo_agent"],
                       gate_pass=False),
        await run_case("clear pass (62)", "ACCEPTED",
                       ["memo_agent"], ["diagnostic_agent"], scores=(16, 27, 19)),
        await run_case("clear reject (30)", "REJECTED_SCORE",
                       ["diagnostic_agent"], ["memo_agent"], scores=(10, 12, 8)),
        await run_case("exactly at cutoff (60)", "ACCEPTED",
                       ["memo_agent"], ["diagnostic_agent"], scores=(20, 20, 20)),
        await run_case("one below cutoff (59)", "REJECTED_SCORE",
                       ["diagnostic_agent"], ["memo_agent"], scores=(20, 20, 19)),
        await run_case("judge gives wrong answer, Python overrides", "REJECTED_SCORE",
                       ["diagnostic_agent"], ["memo_agent"], scores=(10, 12, 8),
                       judge_lies={"final_score": 75, "decision": "ACCEPTED"}),
    ]
    print(f"\n{sum(results)} of {len(results)} routing tests passed")


asyncio.run(main())
