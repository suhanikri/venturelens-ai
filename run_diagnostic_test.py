import asyncio
import json
from dotenv import load_dotenv
from google.adk.runners import InMemoryRunner
from google.genai import types

from agents.diagnostic_agent import diagnostic_agent

load_dotenv()

SAMPLE_REJECTION_INPUT = {
  "report_type": "SCORE_BELOW_CUTOFF",
  "final_score": 30,
  "cutoff": 60,
  "sub_scores": {"market_tam": 10, "financial_cacltv": 12, "traction_moat": 8},
  "scorer_details": [
    {
      "agent": "market_tam",
      "findings": {"tam_realistic": False, "flags": ["Market size figures not disclosed with supporting data"]},
      "reasoning_summary": "Market claims lack grounding and specificity."
    },
    {
      "agent": "financial_cacltv",
      "findings": {"cac_ltv_ratio": 1.2, "margins_healthy": False, "flags": ["LTV:CAC ratio below 2x", "Burn rate significantly exceeds revenue"]},
      "reasoning_summary": "Weak unit economics with unsustainable burn relative to revenue."
    },
    {
      "agent": "traction_moat",
      "findings": {"customer_validation": False, "defensibility": "none", "flags": ["No paying customers disclosed", "No competitive differentiation identified"]},
      "reasoning_summary": "Minimal traction and no clear moat against competitors."
    }
  ]
}

runner = InMemoryRunner(agent=diagnostic_agent, app_name="venturelens")

async def main():
    session = await runner.session_service.create_session(
        app_name="venturelens", user_id="test_user"
    )

    user_message = types.Content(
        role="user",
        parts=[types.Part(text=json.dumps(SAMPLE_REJECTION_INPUT))]
    )

    full_response_text = ""
    async for event in runner.run_async(
        user_id="test_user",
        session_id=session.id,
        new_message=user_message
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    full_response_text += part.text

    print("---RAW RESPONSE---")
    print(full_response_text)

    try:
        parsed = json.loads(full_response_text)
        print("\n---PARSED SUCCESSFULLY---")
        print(json.dumps(parsed, indent=2))
    except json.JSONDecodeError as e:
        print("\n---JSON PARSE FAILED---")
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
