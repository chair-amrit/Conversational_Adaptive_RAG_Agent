import json
from pathlib import Path

from langchain_chroma import Chroma

BASE = Path(__file__).resolve().parent

with open(
    BASE / "retrieval_baseline_results.json",
    encoding="utf-8"
) as file:
    results = json.load(file)["results"]

db = Chroma(
    collection_name="my_rag_multiformat",
    persist_directory="./chroma_db"
)

# Inspect the four XLSX queries and Q03.
selected = {"Q03", "Q13", "Q14", "Q15", "Q16"}

for result in results:
    if result["question_id"] not in selected:
        continue

    chunks = result["retrieved_chunks"]
    ids = [chunk["chunk_id"] for chunk in chunks]

    stored = db.get(
        ids=ids,
        include=["documents", "metadatas"]
    )

    documents = dict(zip(stored["ids"], stored["documents"]))
    metadata = dict(zip(stored["ids"], stored["metadatas"]))

    print("\n" + "=" * 75)
    print(result["question_id"], result["question"])
    print("Expected:", result["expected_source"])

    for chunk in chunks:
        chunk_id = chunk["chunk_id"]
        meta = metadata[chunk_id]

        print(
            f"\nRank: {chunk['rank']} | "
            f"Source: {chunk['source_file']} | "
            f"Chunk: {meta.get('chunk_index')}"
        )

        print("Content:", documents[chunk_id][:250].replace("\n", " "))