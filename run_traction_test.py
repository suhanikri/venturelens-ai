import asyncio
import json
from dotenv import load_dotenv
from google.adk.runners import InMemoryRunner
from google.genai import types

from agents.traction_agent import traction_agent

load_dotenv()

SAMPLE_EXTRACTED_JSON = {
  "founder_info": {"startup_name": "EcoCart", "sector": "Sustainable E-commerce"},
  "pitch_content": {
    "solution": "EcoCart provides a plug-in analytics dashboard that helps online stores switch to sustainable packaging and track carbon footprint per order.",
    "traction_metrics": {
      "customers": "340 paying merchants",
      "mrr": "INR 1.5 Lakhs",
      "growth_rate": "22% month-over-month"
    }
  }
}

runner = InMemoryRunner(agent=traction_agent, app_name="venturelens")

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
