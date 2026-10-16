from concurrent.futures import ThreadPoolExecutor
from services.vector_service import search_chunks
from llm import ask
from tavily import TavilyClient
from config import TAVILY_API_KEY
from services.guardrails import validate_query, harden_context, grade_chunk
from services.router import CLASSIFIER_PROMPT, route_by_retrieval, parse_classifier_output, filter_by_score

tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

TOP_K = 3


def classify_query(query: str, top_score: float, source: str = None) -> str:
    # Step 1: check retrieval confidence FIRST, before asking the LLM to guess
    route = route_by_retrieval(top_score, source)
    if route:
        return route

    # Step 2: only ask the LLM to decide between direct vs web
    return parse_classifier_output(ask(system_prompt=CLASSIFIER_PROMPT, user_prompt=query))


def grade_chunks(query: str, chunks: list[dict]) -> list[dict]:
    """Grades all chunks concurrently; LLM calls are I/O-bound so threads overlap them."""
    if not chunks:
        return []
    with ThreadPoolExecutor(max_workers=len(chunks)) as pool:
        verdicts = list(pool.map(lambda c: grade_chunk(ask, query, c["text"]), chunks))
    return [c for c, ok in zip(chunks, verdicts) if ok]


def answer_from_web(query: str, fallback: bool = False) -> dict:
    search_results = tavily_client.search(query, max_results=3)
    context = "\n\n".join([r["content"] for r in search_results["results"]])

    answer = ask(
        system_prompt="Answer using this current web search context:\n\n" + harden_context(context),
        user_prompt=query
    )
    return {
        "answer": answer,
        "sources": [{"text": r["content"], "url": r["url"]} for r in search_results["results"]],
        "route": "web",
        "fallback": fallback
    }


def answer_question(query: str, source: str = None) -> dict:
    error = validate_query(query)

    if error:
        return {"answer": error, "sources": [], "route": "rejected"}

    # One retrieval serves both the routing decision and the RAG context.
    results = search_chunks(query, top_k=TOP_K, source=source)
    top_score = results[0]["score"] if results else 0

    route = classify_query(query, top_score, source=source)

    if route == "not_found_in_source":
        return {"answer": f"No relevant information found in {source}.", "sources": [], "route": "rag"}

    if route == "web":
        return answer_from_web(query)

    if route == "direct":
        answer = ask(
            system_prompt="You are a helpful assistant. Answer directly from general knowledge.",
            user_prompt=query
        )
        return {"answer": answer, "sources": [], "route": "direct"}

    # route == "rag"
    graded_results = grade_chunks(query, filter_by_score(results))

    if not graded_results:
        if source:
            # The user scoped the question to one document; don't silently leave it.
            return {"answer": f"No relevant information found in {source}.", "sources": [], "route": "rag"}
        # Corrective RAG: retrieved chunks were judged irrelevant, so fall back to web search.
        return answer_from_web(query, fallback=True)

    context = "\n\n".join([r["text"] for r in graded_results])

    answer = ask(
        system_prompt="Answer the question using only this context:\n\n" + harden_context(context),
        user_prompt=query
    )

    return {
        "answer": answer,
        "sources": graded_results,
        "route": "rag"
    }
