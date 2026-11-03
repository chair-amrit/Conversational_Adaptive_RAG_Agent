import json
from pathlib import Path
from collections import Counter

path = Path(__file__).resolve().parent / "retrieval_baseline_results.json"

with path.open("r", encoding="utf-8") as file:
    data = json.load(file)

for result in data["results"]:
    relevant_ids = set(result["relevant_chunk_ids"])
    chunks = result["retrieved_chunks"]

    ranks = [
        chunk["rank"]
        for chunk in chunks
        if chunk["chunk_id"] in relevant_ids
    ]

    source_counts = Counter(
        chunk["source_file"] for chunk in chunks
    )

    print("\n" + "=" * 65)
    print(result["question_id"], result["question"])
    print("Expected source:", result["expected_source"])
    print("Relevant chunk rank:", ranks or "Not retrieved")
    print("Top-10 source distribution:", dict(source_counts))
    print("Top-ranked source:", chunks[0]["source_file"] if chunks else "None")