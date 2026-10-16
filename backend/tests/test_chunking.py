from services.chunking_service import chunk_text


def test_empty_text_has_no_chunks():
    assert chunk_text("") == []


def test_short_text_is_single_chunk():
    assert chunk_text("hello world") == ["hello world"]


def test_chunks_respect_size_and_overlap():
    text = "".join(chr(ord("a") + i % 26) for i in range(2500))
    chunks = chunk_text(text, chunk_size=1000, overlap=150)

    assert all(len(c) <= 1000 for c in chunks)
    # Each chunk starts 850 chars after the previous one, so consecutive chunks share 150 chars.
    for prev, nxt in zip(chunks, chunks[1:]):
        assert prev[-150:] == nxt[:150]


def test_chunks_cover_entire_text():
    text = "x" * 1234 + "END"
    chunks = chunk_text(text, chunk_size=500, overlap=100)
    assert chunks[0].startswith("x")
    assert chunks[-1].endswith("END")
