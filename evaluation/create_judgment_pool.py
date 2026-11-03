import csv
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

# Collect all top-5 chunk IDs.
all_ids = list(dict.fromkeys(
    chunk["chunk_id"]
    for result in results
    for chunk in result["retrieved_chunks"][:5]
))

stored = db.get(
    ids=all_ids,
    include=["documents", "metadatas"]
)

content_by_id = dict(zip(stored["ids"], stored["documents"]))
metadata_by_id = dict(zip(stored["ids"], stored["metadatas"]))

output_path = BASE / "retrieval_judgment_pool.csv"

fields = [
    "question_id",
    "question",
    "expected_source",
    "rank",
    "retrieved_source",
    "chunk_index",
    "chunk_id",
    "content",
    "relevance"
]

with output_path.open(
    "w",
    newline="",
    encoding="utf-8-sig"
) as file:
    writer = csv.DictWriter(file, fieldnames=fields)
    writer.writeheader()

    for result in results:
        known_relevant = set(result["relevant_chunk_ids"])

        for chunk in result["retrieved_chunks"][:5]:
            chunk_id = chunk["chunk_id"]
            metadata = metadata_by_id[chunk_id]

            writer.writerow({
                "question_id": result["question_id"],
                "question": result["question"],
                "expected_source": result["expected_source"],
                "rank": chunk["rank"],
                "retrieved_source": metadata.get("file_name"),
                "chunk_index": metadata.get("chunk_index"),
                "chunk_id": chunk_id,
                "content": content_by_id[chunk_id],
                "relevance": (
                    1 if chunk_id in known_relevant else ""
                )
            })

print("Judgement pool created:", output_path)
print("Questions:", len(results))
print("Judgements:", len(results) * 5)