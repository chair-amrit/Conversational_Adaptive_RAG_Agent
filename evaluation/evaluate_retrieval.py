import json
from pathlib import Path
from statistics import mean

from langchain_chroma import Chroma
from rag_utils import GoogleGenerativeAIEmbeddings


# Configuration
BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "retrieval_eval_dataset.json"
RESULT_PATH = BASE_DIR / "retrieval_baseline_results.json"

COLLECTION_NAME = "my_rag_multiformat"
PERSIST_DIR = "./chroma_db"
K = 10


def load_dataset():
    with DATASET_PATH.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def validate_ground_truth(db, test_cases):
    gold_ids = list(dict.fromkeys(
        chunk_id
        for case in test_cases
        for chunk_id in case["relevant_chunk_ids"]
    ))

    stored = db.get(
        ids=gold_ids,
        include=["metadatas"]
    )

    metadata_by_id = dict(
        zip(stored["ids"], stored["metadatas"])
    )

    missing = set(gold_ids) - set(metadata_by_id)

    if missing:
        raise ValueError(
            f"Missing ground-truth chunk IDs: {missing}"
        )

    for case in test_cases:
        for chunk_id in case["relevant_chunk_ids"]:
            actual_source = metadata_by_id[chunk_id].get("file_name")

            if actual_source != case["source_file"]:
                raise ValueError(
                    f"Incorrect source label for {case['id']}: "
                    f"{chunk_id} belongs to {actual_source}"
                )

    print("Ground-truth validation passed.")


def calculate_metrics(retrieved_ids, relevant_ids, k):
    top_k = retrieved_ids[:k]

    hits = len(set(top_k) & set(relevant_ids))

    precision = hits / len(top_k) if top_k else 0.0
    recall = hits / len(relevant_ids) if relevant_ids else 0.0

    reciprocal_rank = 0.0

    for rank, chunk_id in enumerate(top_k, start=1):
        if chunk_id in relevant_ids:
            reciprocal_rank = 1 / rank
            break

    return {
        "precision_at_k": precision,
        "recall_at_k": recall,
        "reciprocal_rank": reciprocal_rank,
    }


def evaluate():
    dataset = load_dataset()
    test_cases = dataset["test_cases"]

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001"
    )

    db = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=PERSIST_DIR,
        embedding_function=embeddings
    )

    validate_ground_truth(db, test_cases)

    # Embed evaluation questions using query embeddings.
    query_vectors = [
        embeddings.embed_query(case["question"])
        for case in test_cases
    ]

    # Retrieve actual Chroma IDs and their ranking.
    results = db._collection.query(
        query_embeddings=query_vectors,
        n_results=K,
        include=["documents", "metadatas", "distances"]
    )

    evaluation_results = []

    for index, case in enumerate(test_cases):
        retrieved_ids = results["ids"][index]
        relevant_ids = set(case["relevant_chunk_ids"])

        metrics = calculate_metrics(
            retrieved_ids,
            relevant_ids,
            K
        )

        retrieved_chunks = []

        for rank, chunk_id in enumerate(retrieved_ids, start=1):
            metadata = results["metadatas"][index][rank - 1]

            retrieved_chunks.append({
                "rank": rank,
                "chunk_id": chunk_id,
                "source_file": metadata.get("file_name"),
                "distance": results["distances"][index][rank - 1]
            })

        evaluation_results.append({
            "question_id": case["id"],
            "question": case["question"],
            "expected_source": case["source_file"],
            "relevant_chunk_ids": list(relevant_ids),
            "retrieved_chunks": retrieved_chunks,
            "metrics": metrics
        })

        print(
            f"{case['id']} | "
            f"P@{K}: {metrics['precision_at_k']:.3f} | "
            f"R@{K}: {metrics['recall_at_k']:.3f} | "
            f"RR: {metrics['reciprocal_rank']:.3f}"
        )

    summary = {
        "total_queries": len(evaluation_results),
        "k": K,
        "precision_at_k": mean(
            x["metrics"]["precision_at_k"]
            for x in evaluation_results
        ),
        "recall_at_k": mean(
            x["metrics"]["recall_at_k"]
            for x in evaluation_results
        ),
        "mrr": mean(
            x["metrics"]["reciprocal_rank"]
            for x in evaluation_results
        )
    }

    output = {
        "dataset": dataset["dataset_name"],
        "evaluation": "baseline",
        "summary": summary,
        "results": evaluation_results
    }

    with RESULT_PATH.open("w", encoding="utf-8") as file:
        json.dump(output, file, indent=2)

    print("\n========== BASELINE SUMMARY ==========")
    print(f"Queries: {summary['total_queries']}")
    print(f"Precision@{K}: {summary['precision_at_k']:.4f}")
    print(f"Recall@{K}: {summary['recall_at_k']:.4f}")
    print(f"MRR: {summary['mrr']:.4f}")
    print(f"\nDetailed results saved to: {RESULT_PATH}")


if __name__ == "__main__":
    evaluate()