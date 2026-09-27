import asyncio
import json
from dotenv import load_dotenv
from google.adk.runners import InMemoryRunner
from google.genai import types

from agents.gatekeeper_agent import gatekeeper_agent

load_dotenv()

# This is the actual output we got from the Extraction Agent test
SAMPLE_EXTRACTED_JSON = {
  "founder_info": {"startup_name": "EcoCart", "sector": "Sustainable E-commerce"},
  "gst_details": {
    "gst_number": "27AABCE1234F1Z5",
    "registration_date": "14/03/2023",
    "validity_status": "Active"
  },
  "pitch_content": {
    "problem_statement": "Small retailers lack affordable tools to track and reduce packaging waste.",
    "solution": "EcoCart provides a plug-in analytics dashboard.",
    "market_claims": {"tam": "$12 Billion", "sam": "$2 Billion", "som": "$50 Million"},
    "financials": {"revenue": "INR 18 Lakhs", "cac": "INR 450", "ltv": "INR 3200", "burn_rate": "INR 2 Lakhs"},
    "traction_metrics": {"customers": "340", "mrr": "INR 1.5 Lakhs", "growth_rate": "22%"},
    "team_info": "Founded by two IIT graduates."
  },
  "extraction_confidence": 1.0
}

runner = InMemoryRunner(agent=gatekeeper_agent, app_name="venturelens")

async def main():
    session = await runner.session_service.create_session(
        app_name="venturelens", user_id="test_user"
    )

    user_message = types.Content(
        role="user",
        parts=[types.Part(text=json.dumps(SAMPLE_EXTRACTED_JSON))]
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
