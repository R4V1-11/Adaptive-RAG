from services.vector_service import search_chunks
from llm import ask
from tavily import TavilyClient
from config import TAVILY_API_KEY
from services.guardrails import validate_query, harden_context, grade_chunk

tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

def classify_query(query: str, source: str = None) -> str:
    # Step 1: check retrieval confidence FIRST, before asking the LLM to guess
    results = search_chunks(query, top_k=1, source=source)
    top_score = results[0]["score"] if results else 0

    if top_score > 0.35:
        return "rag"   # strong evidence it's answerable from documents
    
    if source:
        return "not_found_in_source"
    # Step 2: only ask the LLM to decide between direct vs web
    decision = ask(
        system_prompt="""You are a query classifier.
Reply with ONLY one word: 'direct' or 'web'.
'direct' = general knowledge, unlikely to have changed recently.
'web'    = needs current/live/real-time information (prices, news, live status, today's date).""",
        user_prompt=query
    )
    return "web" if "web" in decision.strip().lower() else "direct"

def answer_question(query: str, source: str = None) -> dict:


    error = validate_query(query)

    if error:
        return {"answer": error, "sources": [], "route": "rejected"}

    route = classify_query(query, source=source)

    if route == "not_found_in_source":
        return {"answer": f"No relevant information found in {source}.", "sources": [], "route": "rag"}

    if route == "web":
        search_results = tavily_client.search(query, max_results=3)
        context = "\n\n".join([r["content"] for r in search_results["results"]])

        answer = ask(
            system_prompt="Answer using this current web search context:\n\n" + harden_context(context),
            user_prompt=query
        )
        return {
            "answer": answer,
            "sources": [{"text": r["content"], "url": r["url"]} for r in search_results["results"]],
            "route": "web"
        }

    if route == "direct":
        answer = ask(
            system_prompt="You are a helpful assistant. Answer directly from general knowledge.",
            user_prompt=query
        )
        return {"answer": answer, "sources": [], "route": "direct"}

    # route == "rag"
    results = search_chunks(query, top_k=3, source=source)
    good_results = [r for r in results if r["score"] > 0.25]

    if not good_results:
        return {"answer": "No relevant information found in the uploaded documents.", "sources": [], "route": "rag"}
    

    graded_results = [r for r in good_results if grade_chunk(ask, query, r["text"])]

    if not graded_results:
        return {"answer": "No relevant information found in the uploaded documents.", "sources": [], "route": "rag"}

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