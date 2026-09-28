import asyncio
import json
from dotenv import load_dotenv
from pipeline import run_pipeline

load_dotenv()


async def main():
    with open("sample_data/dummy_pitch_deck.pdf", "rb") as f:
        pitch = f.read()
    with open("sample_data/dummy_gst_document.pdf", "rb") as f:
        gst = f.read()
    result = await run_pipeline(pitch, gst)
    print(json.dumps(result, indent=2))


asyncio.run(main())
