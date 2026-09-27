import asyncio
import os
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.genai import types

load_dotenv()
print("Loaded key:", os.getenv("GOOGLE_API_KEY"))

# The simplest possible agent
basic_agent = LlmAgent(
    name="test_agent",
    model="gemini-3.8-flash",
    instruction="You are a helpful assistant. Answer briefly."
)

# Run it — explicitly naming the app avoids a separate alignment warning
runner = InMemoryRunner(agent=basic_agent, app_name="test_app")

async def main():
    session = await runner.session_service.create_session(
        app_name="test_app", user_id="test_user"
    )

    user_message = types.Content(
        role="user",
        parts=[types.Part(text="Say hello and confirm you're working.")]
    )

    async for event in runner.run_async(
        user_id="test_user",
        session_id=session.id,
        new_message=user_message
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print("Agent response:", part.text)

if __name__ == "__main__":
    asyncio.run(main())