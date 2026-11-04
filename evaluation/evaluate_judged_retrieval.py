import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

BASE_DIR = Path(__file__).resolve().parent

CSV_PATH = (
    BASE_DIR.parent
    / "prac_files"
    / "retrieval_judgment_pool_completed.csv"
)

OUTPUT_PATH = BASE_DIR / "retrieval_judged_results.json"

K = 5


def load_judgements():
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Judgement file not found: {CSV_PATH}"
        )

    grouped = defaultdict(list)

    with CSV_PATH.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)

        required = {
            "question_id", "rank", "chunk_id", "relevance"
        }

        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Required CSV columns are missing.")

        for row in reader:
            label = row["relevance"].strip()

            if label not in {"0", "1"}:
                raise ValueError(
                    f"Invalid relevance label in {row['question_id']}"
                )

            grouped[row["question_id"]].append(row)

    if not grouped:
        raise ValueError("No evaluation judgements found.")

    for question_id, rows in grouped.items():
        rows.sort(key=lambda x: int(x["rank"]))
        ranks = [int(row["rank"]) for row in rows]

        if ranks != list(range(1, K + 1)):
            raise ValueError(
                f"{question_id}: expected ranks 1-{K}, got {ranks}"
            )

        chunk_ids = [row["chunk_id"] for row in rows]

        if len(set(chunk_ids)) != K:
            raise ValueError(
                f"{question_id}: duplicate chunk IDs detected."
            )

    return grouped


def evaluate():
    grouped = load_judgements()

    results = []

    for question_id, rows in sorted(grouped.items()):
        relevant_ranks = [
            int(row["rank"])
            for row in rows
            if row["relevance"].strip() == "1"
        ]

        relevant_count = len(relevant_ranks)

        precision = relevant_count / K

        reciprocal_rank = (
            1 / relevant_ranks[0]
            if relevant_ranks else 0.0
        )

        hit = 1 if relevant_ranks else 0

        results.append({
            "question_id": question_id,
            "relevant_count": relevant_count,
            "relevant_ranks": relevant_ranks,
            "precision_at_5": precision,
            "reciprocal_rank": reciprocal_rank,
            "hit_at_5": hit
        })

        print(
            f"{question_id} | "
            f"Relevant: {relevant_count}/{K} | "
            f"P@5: {precision:.3f} | "
            f"RR: {reciprocal_rank:.3f}"
        )

    summary = {
        "total_queries": len(results),
        "total_judgements": len(results) * K,
        "total_relevant": sum(
            item["relevant_count"] for item in results
        ),
        "total_irrelevant": (
            len(results) * K
            - sum(item["relevant_count"] for item in results)
        ),
        "precision_at_5": mean(
            item["precision_at_5"] for item in results
        ),
        "mrr_at_5": mean(
            item["reciprocal_rank"] for item in results
        ),
        "hit_rate_at_5": mean(
            item["hit_at_5"] for item in results
        ),
        "label_method": "LLM-assisted relevance judgements"
    }

    output = {
        "evaluation": "judged_retrieval_v1",
        "summary": summary,
        "results": results
    }

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(output, file, indent=2)

    print("\n========== JUDGED EVALUATION SUMMARY ==========")
    for metric, value in summary.items():
        print(f"{metric}: {value}")

    print(f"\nResults saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    evaluate()
