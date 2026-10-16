from services.router import (
    CHUNK_SCORE_THRESHOLD,
    RAG_ROUTE_THRESHOLD,
    filter_by_score,
    parse_classifier_output,
    route_by_retrieval,
)


def test_high_score_routes_to_rag():
    assert route_by_retrieval(RAG_ROUTE_THRESHOLD + 0.01, None) == "rag"
    assert route_by_retrieval(0.9, "doc.pdf") == "rag"


def test_low_score_scoped_query_is_not_found():
    assert route_by_retrieval(0.1, "doc.pdf") == "not_found_in_source"


def test_low_score_unscoped_query_defers_to_llm():
    assert route_by_retrieval(0.1, None) is None
    assert route_by_retrieval(RAG_ROUTE_THRESHOLD, None) is None  # threshold is exclusive


def test_parse_classifier_output():
    assert parse_classifier_output("web") == "web"
    assert parse_classifier_output("  WEB\n") == "web"
    assert parse_classifier_output("direct") == "direct"
    assert parse_classifier_output("unsure") == "direct"


def test_filter_by_score():
    results = [{"score": 0.9}, {"score": CHUNK_SCORE_THRESHOLD}, {"score": 0.1}]
    assert filter_by_score(results) == [{"score": 0.9}]
