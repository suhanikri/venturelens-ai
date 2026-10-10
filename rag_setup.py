"""Creates the VentureLens knowledge base in Vertex AI RAG Engine and imports a
Google Drive folder. Safe to run again to add new documents.
  python rag_setup.py <Google Drive folder link>"""
import os
import re
import sys

from dotenv import load_dotenv

load_dotenv()
import agentplatform
from agentplatform import types

if len(sys.argv) < 2:
    sys.exit("Usage: python rag_setup.py <Google Drive folder link>")
link = sys.argv[1]

match = re.search(r"/folders/([A-Za-z0-9_-]+)", link)
kind = "RESOURCE_TYPE_FOLDER"
if not match:
    match = re.search(r"/d/([A-Za-z0-9_-]+)", link)
    kind = "RESOURCE_TYPE_FILE"
if not match:
    sys.exit("Could not find a Google Drive folder or file id in that link.")
resource_id = match.group(1)

PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("RAG_LOCATION", "asia-south1")
NAME = "venturelens-knowledge"
client = agentplatform.Client(project=PROJECT, location=LOCATION)

existing = getattr(client.rag.list_corpora(), "rag_corpora", None) or []
corpus = next((c for c in existing if c.display_name == NAME), None)
if corpus:
    print("Using existing knowledge base:", corpus.name)
else:
    corpus = client.rag.create_corpus(rag_corpus=types.RagCorpus(display_name=NAME))
    print("Created knowledge base:", corpus.name)
if not corpus.name:
    sys.exit(f"The knowledge base has no name, so it cannot be used: {corpus}")

try:
    config = types.ImportRagFilesConfig(
        google_drive_source={"resource_ids": [{"resource_id": resource_id, "resource_type": kind}]}
    )
except Exception as e:
    print("Could not build the Drive source:", e)
    print("resource_ids expects:", types.GoogleDriveSource.model_fields["resource_ids"].annotation)
    sys.exit(1)

print("Importing documents (this can take a few minutes)...")
result = client.rag.import_files(name=corpus.name, import_config=config)
print(result)

try:
    files = getattr(client.rag.list_files(name=corpus.name), "rag_files", None) or []
    print(f"Documents in the knowledge base: {len(files)}")
    for f in files:
        print("  -", getattr(f, "display_name", f))
except Exception as e:
    print("(could not list the files:", e, ")")

env = open(".env").read() if os.path.exists(".env") else ""
if "RAG_CORPUS=" not in env:
    with open(".env", "a") as f:
        f.write(f"\nRAG_CORPUS={corpus.name}\nRAG_LOCATION={LOCATION}\n")
    print("Saved RAG_CORPUS to .env")
