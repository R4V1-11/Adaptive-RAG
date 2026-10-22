from services.vector_service import create_collection, add_chunk, search_chunks


create_collection()

add_chunk("Ravi knows TypeScript, React Native, Go, and Java.", {"source": "test"})
add_chunk("Ravi enjoys badminton and gym training.", {"source": "test"})

print("Done adding chunks!")

# NEW — test search
results = search_chunks("what programming languages does Ravi know?")

print("Search results:")
for r in results:
    print(f"Score: {r['score']:.2f} → {r['text']}")