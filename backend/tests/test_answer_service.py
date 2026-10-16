import pytest

from services import answer_service as svc


@pytest.fixture
def fake_web(monkeypatch):
    calls = []

    def answer_from_web(query, fallback=False):
        calls.append(fallback)
        return {"answer": "web answer", "sources": [], "route": "web", "fallback": fallback}

    monkeypatch.setattr(svc, "answer_from_web", answer_from_web)
    return calls


def make_llm(grades: dict[str, bool], classifier: str = "direct"):
    """Fake LLM: grader verdicts keyed by chunk text, fixed classifier output, echo answers."""
    def ask(system_prompt, user_prompt):
        if "relevance grader" in system_prompt:
            text = user_prompt.split("Text: ", 1)[1]
            return "yes" if grades.get(text) else "no"
        if "query classifier" in system_prompt:
            return classifier
        return "generated answer"
    return ask


def chunks(*specs):
    return [{"text": t, "score": s, "source": "doc.pdf"} for t, s in specs]


def test_rejected_query(monkeypatch):
    result = svc.answer_question("")
    assert result["route"] == "rejected"


def test_rag_answer_cites_only_graded_chunks(monkeypatch):
    monkeypatch.setattr(svc, "search_chunks", lambda *a, **k: chunks(("good", 0.8), ("bad", 0.6)))
    monkeypatch.setattr(svc, "ask", make_llm({"good": True, "bad": False}))

    result = svc.answer_question("question")

    assert result["route"] == "rag"
    assert [s["text"] for s in result["sources"]] == ["good"]


def test_corrective_fallback_to_web_when_all_chunks_rejected(monkeypatch, fake_web):
    monkeypatch.setattr(svc, "search_chunks", lambda *a, **k: chunks(("a", 0.8), ("b", 0.7)))
    monkeypatch.setattr(svc, "ask", make_llm({}))

    result = svc.answer_question("question")

    assert result["route"] == "web"
    assert fake_web == [True]


def test_scoped_query_does_not_fall_back_to_web(monkeypatch, fake_web):
    monkeypatch.setattr(svc, "search_chunks", lambda *a, **k: chunks(("a", 0.8)))
    monkeypatch.setattr(svc, "ask", make_llm({}))

    result = svc.answer_question("question", source="doc.pdf")

    assert result["route"] == "rag"
    assert "No relevant information" in result["answer"]
    assert fake_web == []


def test_low_score_uses_classifier(monkeypatch, fake_web):
    monkeypatch.setattr(svc, "search_chunks", lambda *a, **k: chunks(("a", 0.1)))

    monkeypatch.setattr(svc, "ask", make_llm({}, classifier="direct"))
    assert svc.answer_question("what is 2+2")["route"] == "direct"

    monkeypatch.setattr(svc, "ask", make_llm({}, classifier="web"))
    assert svc.answer_question("bitcoin price today")["route"] == "web"
    assert fake_web == [False]


def test_grading_runs_in_parallel(monkeypatch):
    import threading
    import time

    barrier = threading.Barrier(3, timeout=2)

    def ask(system_prompt, user_prompt):
        if "relevance grader" in system_prompt:
            barrier.wait()  # deadlocks (times out) unless all 3 graders run concurrently
            return "yes"
        return "answer"

    monkeypatch.setattr(svc, "search_chunks", lambda *a, **k: chunks(("a", 0.9), ("b", 0.8), ("c", 0.7)))
    monkeypatch.setattr(svc, "ask", ask)

    start = time.perf_counter()
    result = svc.answer_question("question")
    assert result["route"] == "rag"
    assert len(result["sources"]) == 3
    assert time.perf_counter() - start < 2
