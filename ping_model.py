import asyncio
import logging
import sys
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.genai import types

logging.disable(logging.CRITICAL)
load_dotenv()

model_name = sys.argv[1] if len(sys.argv) > 1 else "gemini-3.8-flash"

agent = LlmAgent(
    name="ping_agent",
    model=Gemini(model=model_name, retry_options=types.HttpRetryOptions(attempts=1)),
    instruction="Reply with the single word OK.",
)
runner = InMemoryRunner(agent=agent, app_name="ping")

async def main():
    session = await runner.session_service.create_session(app_name="ping", user_id="u")
    msg = types.Content(role="user", parts=[types.Part(text="ping")])
    try:
        async for event in runner.run_async(user_id="u", session_id=session.id, new_message=msg):
            if event.content and event.content.parts:
                for p in event.content.parts:
                    if p.text:
                        print(f"[{model_name}] replied:", p.text.strip())
    except Exception as e:
        print(f"[{model_name}] FAILED:", str(e)[:200])

asyncio.run(main())