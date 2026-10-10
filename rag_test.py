"""Ask the knowledge base a question:  python rag_test.py "how to build a bottom-up TAM" """
import sys

from dotenv import load_dotenv

load_dotenv()
import knowledge

query = " ".join(sys.argv[1:]) or "market sizing"
results = knowledge.search(query)
if not results:
    print("No results.")
for i, c in enumerate(results, 1):
    print(f"--- result {i} | {c['source']}")
    print(c["text"][:500])
