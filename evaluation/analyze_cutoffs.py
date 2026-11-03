import json
from pathlib import Path
from statistics import mean

BASE = Path(__file__).resolve().parent

with open(
    BASE / "retrieval_baseline_results.json",
    encoding="utf-8"
) as file:
    data = json.load(file)

results = data["results"]

for k in (5, 10):
    precisions = []
    recalls = []
    reciprocal_ranks = []
    source_shares = []

    for result in results:
        chunks = result["retrieved_chunks"][:k]
        relevant = set(result["relevant_chunk_ids"])

        retrieved_ids = [
            chunk["chunk_id"] for chunk in chunks
        ]

        hits = len(set(retrieved_ids) & relevant)

        precision = hits / len(chunks) if chunks else 0
        recall = hits / len(relevant) if relevant else 0

        rr = 0
        for rank, chunk_id in enumerate(retrieved_ids, 1):
            if chunk_id in relevant:
                rr = 1 / rank
                break

        expected_source = result["expected_source"]

        source_share = (
            sum(
                chunk["source_file"] == expected_source
                for chunk in chunks
            ) / len(chunks)
            if chunks else 0
        )

        precisions.append(precision)
        recalls.append(recall)
        reciprocal_ranks.append(rr)
        source_shares.append(source_share)

    print(f"\n========== TOP {k} RESULTS ==========")
    print(f"Precision@{k}: {mean(precisions):.4f}")
    print(f"Recall@{k}: {mean(recalls):.4f}")
    print(f"MRR@{k}: {mean(reciprocal_ranks):.4f}")
    print(
        f"Expected-source share@{k}: "
        f"{mean(source_shares):.4f}"
    )