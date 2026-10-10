"""Retrieval from the VentureLens knowledge base (Vertex AI RAG Engine).
Returns [] when RAG is not configured or fails, so the pipeline never breaks."""
import asyncio
import os

TOP_K = 4
MAX_QUERIES = 6


def _queries(items):
    """Turn rejection drivers (failed criteria, or scorer flags) into search queries."""
    out = []
    for it in items or []:
        if isinstance(it, str):
            out.append(it)
        elif isinstance(it, dict):
            findings = it.get("findings") or {}
            flags = findings.get("flags") or []
            out.extend(str(f) for f in flags)
            if not flags and it.get("reasoning_summary"):
                out.append(str(it["reasoning_summary"]))
    seen, unique = set(), []
    for q in (q.strip() for q in out):
        if q and q not in seen:
            seen.add(q)
            unique.append(q)
    return unique[:MAX_QUERIES]


def search(query, top_k=TOP_K):
    """One query against the knowledge base. Returns a list of {source, text}."""
    import agentplatform

    client = agentplatform.Client(project=os.getenv("GOOGLE_CLOUD_PROJECT"),
                                  location=os.getenv("RAG_LOCATION", "asia-south1"))
    resp = client.rag.retrieve_contexts(
        vertex_rag_store={"rag_resources": [{"rag_corpus": os.getenv("RAG_CORPUS")}]},
        query={"text": query, "similarity_top_k": top_k},
    )
    contexts = getattr(getattr(resp, "contexts", None), "contexts", None) or []
    return [{"source": getattr(c, "source_display_name", None) or getattr(c, "source_uri", ""),
             "text": c.text} for c in contexts]


def _retrieve(queries):
    if not os.getenv("RAG_CORPUS") or not queries:
        return []
    found, seen = [], set()
    for q in queries:
        for c in search(q):
            key = (c["source"], c["text"][:80])
            if key in seen:
                continue
            seen.add(key)
            found.append({"source": c["source"], "text": c["text"][:1200]})
    return found[:8]


async def find_passages(items):
    try:
        return await asyncio.to_thread(_retrieve, _queries(items))
    except Exception as e:
        print(f"[knowledge] retrieval skipped: {e}")
        return []
