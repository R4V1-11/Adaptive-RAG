"""Evaluates the query router and retriever against a labelled dataset.

Indexes a small fictional corpus (eval/corpus/*.txt) into a separate Qdrant
collection, then measures:
  - routing accuracy: does each query take its expected route (rag / web / direct)?
  - retrieval quality: for document questions, is the chunk containing the
    answer retrieved (hit@1, hit@k, MRR)?
  - with --full: end-to-end route taken by answer_question(), including
    corrective web fallbacks, and whether RAG answers contain the evidence.

Requires Qdrant running and GROQ_API_KEY (plus TAVILY_API_KEY for --full).

Usage (from backend/):
    python eval/run_eval.py [--full] [--reindex] [--out eval/results.json]
"""
import argparse
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVAL_DIR.parent))
# Use a dedicated collection so evaluation never touches user documents.
os.environ.setdefault("QDRANT_COLLECTION", "eval_documents")

from services import vector_service as vs  # noqa: E402
from services.chunking_service import chunk_text  # noqa: E402
from services.answer_service import TOP_K, answer_question, classify_query  # noqa: E402

ROUTES = ["rag", "web", "direct"]


def with_retry(fn, *args, attempts=4, **kwargs):
    """Retries transient API failures (e.g. LLM rate limits) with exponential backoff."""
    for i in range(attempts):
        try:
            return fn(*args, **kwargs)
        except Exception as e:  # noqa: BLE001
            if i == attempts - 1:
                raise
            wait = 2 ** (i + 1)
            print(f"  ! {type(e).__name__}: {e} — retrying in {wait}s")
            time.sleep(wait)


def index_corpus(reindex: bool):
    if reindex and vs.client.collection_exists(vs.COLLECTION_NAME):
        vs.client.delete_collection(vs.COLLECTION_NAME)
    vs.create_collection()

    indexed = {d["name"] for d in vs.list_sources()}
    for path in sorted((EVAL_DIR / "corpus").glob("*.txt")):
        if path.name in indexed:
            continue
        chunks = chunk_text(path.read_text(encoding="utf-8"))
        vs.add_chunks(chunks, {"source": path.name})
        print(f"Indexed {path.name}: {len(chunks)} chunks")


def evaluate_retrieval(item: dict, results: list[dict]) -> dict:
    evidence = item["evidence"].lower()
    rank = next(
        (i + 1 for i, r in enumerate(results)
         if r["source"] == item["source"] and evidence in r["text"].lower()),
        None,
    )
    return {"rank": rank, "top_score": results[0]["score"] if results else 0.0}


def pct(n: int, d: int) -> str:
    return f"{100 * n / d:.1f}% ({n}/{d})" if d else "n/a"


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="also run the full answer pipeline end to end")
    parser.add_argument("--reindex", action="store_true", help="rebuild the eval collection from scratch")
    parser.add_argument("--delay", type=float, default=0.0, help="seconds to sleep between queries (rate limits)")
    parser.add_argument("--out", default=str(EVAL_DIR / "results.json"))
    args = parser.parse_args()

    dataset = json.loads((EVAL_DIR / "dataset.json").read_text(encoding="utf-8"))
    index_corpus(args.reindex)

    records = []
    for item in dataset:
        start = time.perf_counter()
        results = vs.search_chunks(item["query"], top_k=TOP_K)
        top_score = results[0]["score"] if results else 0.0
        predicted = with_retry(classify_query, item["query"], top_score)
        record = {
            **item,
            "predicted_route": predicted,
            "top_score": round(top_score, 4),
            "routing_latency_s": round(time.perf_counter() - start, 3),
        }

        if item["expected_route"] == "rag":
            record["retrieval_rank"] = evaluate_retrieval(item, results)["rank"]

        if args.full:
            start = time.perf_counter()
            response = with_retry(answer_question, item["query"])
            record["final_route"] = response["route"]
            record["fallback"] = bool(response.get("fallback"))
            record["e2e_latency_s"] = round(time.perf_counter() - start, 3)
            if item["expected_route"] == "rag":
                record["answer_has_evidence"] = item["evidence"].lower() in response["answer"].lower()

        mark = "✓" if predicted == item["expected_route"] else "✗"
        print(f"{mark} {item['id']:<7} expected={item['expected_route']:<6} got={predicted:<6} top={top_score:.3f}")
        records.append(record)
        if args.delay:
            time.sleep(args.delay)

    # ---- Routing metrics ----
    correct = sum(r["predicted_route"] == r["expected_route"] for r in records)
    confusion = Counter((r["expected_route"], r["predicted_route"]) for r in records)
    per_route = {}
    for route in ROUTES:
        tp = confusion[(route, route)]
        predicted_n = sum(v for (_, p), v in confusion.items() if p == route)
        actual_n = sum(v for (e, _), v in confusion.items() if e == route)
        per_route[route] = {
            "precision": round(tp / predicted_n, 3) if predicted_n else None,
            "recall": round(tp / actual_n, 3) if actual_n else None,
            "support": actual_n,
        }

    # ---- Retrieval metrics ----
    rag = [r for r in records if r["expected_route"] == "rag"]
    ranks = [r["retrieval_rank"] for r in rag]
    hit1 = sum(rank == 1 for rank in ranks)
    hitk = sum(rank is not None for rank in ranks)
    mrr = sum(1 / rank for rank in ranks if rank) / len(ranks) if ranks else 0.0

    avg_latency = sum(r["routing_latency_s"] for r in records) / len(records)

    summary = {
        "n_queries": len(records),
        "routing_accuracy": round(correct / len(records), 3),
        "per_route": per_route,
        "confusion_matrix": {f"{e}->{p}": n for (e, p), n in sorted(confusion.items())},
        "retrieval": {"hit@1": round(hit1 / len(ranks), 3), f"hit@{TOP_K}": round(hitk / len(ranks), 3), "mrr": round(mrr, 3)},
        "avg_routing_latency_s": round(avg_latency, 3),
    }

    print("\n=== Routing ===")
    print(f"Accuracy: {pct(correct, len(records))}")
    for route, m in per_route.items():
        print(f"  {route:<6} precision={m['precision']}  recall={m['recall']}  n={m['support']}")
    print("Confusion (expected -> predicted):")
    for (e, p), n in sorted(confusion.items()):
        print(f"  {e:<6} -> {p:<6} {n}")

    print("\n=== Retrieval (document questions) ===")
    print(f"Hit@1: {pct(hit1, len(ranks))}   Hit@{TOP_K}: {pct(hitk, len(ranks))}   MRR: {mrr:.3f}")
    print(f"Avg routing latency: {avg_latency:.2f}s")

    if args.full:
        final_correct = sum(r["final_route"] == r["expected_route"] for r in records)
        fallbacks = sum(r["fallback"] for r in records)
        answered = sum(r.get("answer_has_evidence", False) for r in rag)
        avg_e2e = sum(r["e2e_latency_s"] for r in records) / len(records)
        summary["end_to_end"] = {
            "final_route_accuracy": round(final_correct / len(records), 3),
            "corrective_fallbacks": fallbacks,
            "rag_answer_contains_evidence": round(answered / len(rag), 3),
            "avg_latency_s": round(avg_e2e, 3),
        }
        print("\n=== End to end ===")
        print(f"Final route accuracy: {pct(final_correct, len(records))}   corrective fallbacks: {fallbacks}")
        print(f"RAG answers containing the evidence: {pct(answered, len(rag))}")
        print(f"Avg end-to-end latency: {avg_e2e:.2f}s")

    misrouted = [r for r in records if r["predicted_route"] != r["expected_route"]]
    if misrouted:
        print("\nMisrouted queries:")
        for r in misrouted:
            print(f"  [{r['id']}] {r['query']}  (expected {r['expected_route']}, got {r['predicted_route']}, top={r['top_score']})")

    Path(args.out).write_text(json.dumps({"summary": summary, "records": records}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved results to {args.out}")


if __name__ == "__main__":
    main()
