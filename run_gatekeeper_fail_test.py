import asyncio
import json
from dotenv import load_dotenv
from google.adk.runners import InMemoryRunner
from google.genai import types

from agents.gatekeeper_agent import gatekeeper_agent

load_dotenv()

# Deliberately BAD data - missing GST, to test failure routing
SAMPLE_FAILING_JSON = {
  "founder_info": {"startup_name": "ShadyStartup", "sector": "Retail"},
  "gst_details": {
    "gst_number": "not disclosed",
    "registration_date": "not disclosed",
    "validity_status": "not disclosed"
  },
  "pitch_content": {
    "problem_statement": "Some problem.",
    "solution": "Some solution.",
    "market_claims": {"tam": "not disclosed", "sam": "not disclosed", "som": "not disclosed"},
    "financials": {"revenue": "not disclosed", "cac": "not disclosed", "ltv": "not disclosed", "burn_rate": "not disclosed"},
    "traction_metrics": {"customers": "not disclosed", "mrr": "not disclosed", "growth_rate": "not disclosed"},
    "team_info": "not disclosed"
  },
  "extraction_confidence": 0.4
}

runner = InMemoryRunner(agent=gatekeeper_agent, app_name="venturelens")

async def main():
    session = await runner.session_service.create_session(
        app_name="venturelens", user_id="test_user"
    )

    user_message = types.Content(
        role="user",
        parts=[types.Part(text=json.dumps(SAMPLE_FAILING_JSON))]
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
