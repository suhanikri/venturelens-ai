import asyncio
import json
from dotenv import load_dotenv
from google.adk.runners import InMemoryRunner
from google.genai import types

from agents.memo_agent import memo_agent

load_dotenv()

# Built from the real outputs of our earlier EcoCart test runs
SAMPLE_ACCEPTED_INPUT = {
  "founder_info": {"startup_name": "EcoCart", "sector": "Sustainable E-commerce"},
  "pitch_summary": "Plug-in analytics dashboard that helps online stores switch to sustainable packaging and track carbon footprint per order.",
  "final_score": 62,
  "cutoff": 60,
  "sub_scores": {"market_tam": 16, "financial_cacltv": 27, "traction_moat": 19},
  "scorer_details": [
    {
      "agent": "market_tam",
      "findings": {
        "tam_realistic": False,
        "market_size_validated": False,
        "flags": [
          "TAM and SAM measure the physical sustainable packaging market, not the software analytics market",
          "No bottom-up pricing or retailer volume data to justify a $50M SOM within 3 years"
        ]
      },
      "reasoning_summary": "Hierarchy from TAM to SOM is consistent, but the figures measure the wrong market."
    },
    {
      "agent": "financial_cacltv",
      "findings": {
        "cac_ltv_ratio": 7.11,
        "margins_healthy": True,
        "flags": ["Monthly burn of INR 2 Lakhs slightly exceeds monthly revenue of about INR 1.5 Lakhs"]
      },
      "reasoning_summary": "Strong unit economics with a 7.1x LTV:CAC ratio; burn marginally outpaces revenue."
    },
    {
      "agent": "traction_moat",
      "findings": {
        "customer_validation": True,
        "defensibility": "weak",
        "flags": [
          "Low average revenue per merchant suggests limited pricing power",
          "Plug-in analytics dashboard lacks proprietary barriers and is easily replicable"
        ]
      },
      "reasoning_summary": "340 paying merchants and 22% MoM growth, but a weak competitive moat."
    }
  ]
}

runner = InMemoryRunner(agent=memo_agent, app_name="venturelens")

async def main():
    session = await runner.session_service.create_session(
        app_name="venturelens", user_id="test_user"
    )

    user_message = types.Content(
        role="user",
        parts=[types.Part(text=json.dumps(SAMPLE_ACCEPTED_INPUT))]
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
