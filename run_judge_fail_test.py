import asyncio
import json
from dotenv import load_dotenv
from google.adk.runners import InMemoryRunner
from google.genai import types

from agents.judge_agent import judge_agent

load_dotenv()

# Deliberately low scores to test the REJECTED path
SCORER_INPUTS = {
  "cutoff": 60,
  "scorer_outputs": [
    {"agent": "market_tam", "score": 10, "max_score": 30},
    {"agent": "financial_cacltv", "score": 12, "max_score": 30},
    {"agent": "traction_moat", "score": 8, "max_score": 30}
  ]
}

runner = InMemoryRunner(agent=judge_agent, app_name="venturelens")

async def main():
    session = await runner.session_service.create_session(
        app_name="venturelens", user_id="test_user"
    )

    user_message = types.Content(
        role="user",
        parts=[types.Part(text=json.dumps(SCORER_INPUTS))]
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
