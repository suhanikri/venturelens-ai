import asyncio
import json
import os
from dotenv import load_dotenv
from google.adk.runners import InMemoryRunner
from google.genai import types

from agents.extraction_agent import extraction_agent

load_dotenv()

PITCH_DECK_PATH = "sample_data/dummy_pitch_deck.pdf"
GST_DOC_PATH = "sample_data/dummy_gst_document.pdf"

runner = InMemoryRunner(agent=extraction_agent, app_name="venturelens")

async def main():
    session = await runner.session_service.create_session(
        app_name="venturelens", user_id="test_user"
    )

    with open(PITCH_DECK_PATH, "rb") as f:
        pitch_deck_bytes = f.read()

    with open(GST_DOC_PATH, "rb") as f:
        gst_doc_bytes = f.read()

    user_message = types.Content(
        role="user",
        parts=[
            types.Part.from_bytes(data=pitch_deck_bytes, mime_type="application/pdf"),
            types.Part.from_bytes(data=gst_doc_bytes, mime_type="application/pdf"),
            types.Part(text="Extract the data from this pitch deck and GST document.")
        ]
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
