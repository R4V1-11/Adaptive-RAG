"""Pure routing logic, kept free of model/DB imports so it can be unit-tested."""

# Top-1 cosine similarity above which a query is treated as answerable from documents.
RAG_ROUTE_THRESHOLD = 0.35
# Minimum similarity for a retrieved chunk to be sent to the LLM grader.
CHUNK_SCORE_THRESHOLD = 0.25

CLASSIFIER_PROMPT = """You are a query classifier.
Reply with ONLY one word: 'direct' or 'web'.
'direct' = general knowledge, unlikely to have changed recently.
'web'    = needs current/live/real-time information (prices, news, live status, today's date)."""


def route_by_retrieval(top_score: float, source: str | None) -> str | None:
    """Decides the route from retrieval confidence alone.

    Returns "rag", "not_found_in_source", or None when the LLM classifier must decide.
    """
    if top_score > RAG_ROUTE_THRESHOLD:
        return "rag"
    if source:
        return "not_found_in_source"
    return None


def parse_classifier_output(text: str) -> str:
    return "web" if "web" in text.strip().lower() else "direct"


def filter_by_score(results: list[dict]) -> list[dict]:
    return [r for r in results if r["score"] > CHUNK_SCORE_THRESHOLD]
