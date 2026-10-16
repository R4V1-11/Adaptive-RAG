from qdrant_client import QdrantClient
from qdrant_client.models import Filter, MatchValue, FieldCondition, PointStruct, VectorParams, Distance
from sentence_transformers import SentenceTransformer
import uuid

client = QdrantClient(host="localhost", port=6333)

COLLECTION_NAME = "documents"

model = SentenceTransformer('all-MiniLM-L6-v2')

def create_collection():
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        print(f"Collection '{COLLECTION_NAME}' created.")

    else:
        print(f"Collection '{COLLECTION_NAME}' already exists.")


def add_chunk(text: str, metadata: dict):
    add_chunks([text], metadata)


def add_chunks(texts: list[str], metadata: dict):
    """Embeds all chunks in one batch and upserts them in a single request."""
    if not texts:
        return

    vectors = model.encode(texts, batch_size=32).tolist()

    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={"text": text, **metadata}
        )
        for text, vector in zip(texts, vectors)
    ]

    client.upsert(collection_name=COLLECTION_NAME, points=points)


def search_chunks(query: str, top_k: int = 3, source: str = None):
    query_vector = model.encode(query).tolist()

    query_filter = None

    if source:
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="source",
                    match=MatchValue(value=source)
                )
            ]
        )

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=query_filter,
        limit=top_k
    ).points

    return [
        {"text": r.payload["text"], "score": r.score, "source": r.payload.get("source")}
        for r in results
    ]


def list_sources() -> list[dict]:
    """Returns every indexed document with its chunk count."""
    counts: dict[str, int] = {}
    offset = None

    while True:
        points, offset = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=256,
            offset=offset,
            with_payload=["source"],
            with_vectors=False,
        )
        for p in points:
            source = p.payload.get("source")
            if source:
                counts[source] = counts.get(source, 0) + 1
        if offset is None:
            break

    return [{"name": name, "chunks": n} for name, n in sorted(counts.items())]
