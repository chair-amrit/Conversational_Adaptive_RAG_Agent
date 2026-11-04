"""Evaluate judged retrieval quality at cutoffs 1..5.

Input:  evaluation/../prac_files/retrieval_judgment_pool_completed.csv
Outputs: retrieval_cutoff_metrics.csv and retrieval_cutoff_report.md in evaluation/.

Coverage@K below is the fraction of all chunks labelled relevant in the judged
Top-5 pool that are retained within Top-K. It is NOT corpus-level Recall@K.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR.parent / "prac_files" / "retrieval_judgment_pool_completed.csv"
METRICS_CSV_PATH = BASE_DIR / "retrieval_cutoff_metrics.csv"
REPORT_PATH = BASE_DIR / "retrieval_cutoff_report.md"
VALID_RANKS = {1, 2, 3, 4, 5}


def load_judgements(path: Path) -> dict[str, list[dict[str, Any]]]:
    if not path.exists():
        raise FileNotFoundError(
            f"Judgement CSV not found: {path}\n"
            "Expected it at prac_files/retrieval_judgment_pool_completed.csv."
        )

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        required = {"question_id", "rank", "chunk_id", "relevance"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV is missing required columns: {sorted(missing)}")

        for line_number, row in enumerate(reader, start=2):
            question_id = (row.get("question_id") or "").strip()
            chunk_id = (row.get("chunk_id") or "").strip()
            try:
                rank = int(row["rank"])
                relevance = int(row["relevance"])
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid rank/relevance at CSV line {line_number}: {exc}"
                ) from exc

            if not question_id or not chunk_id:
                raise ValueError(f"Missing question_id/chunk_id at line {line_number}")
            if rank not in VALID_RANKS:
                raise ValueError(f"Rank must be 1..5 at CSV line {line_number}: {rank}")
            if relevance not in (0, 1):
                raise ValueError(
                    f"Relevance must be 0 or 1 at CSV line {line_number}: {relevance}"
                )

            row["rank"] = rank
            row["relevance"] = relevance
            grouped[question_id].append(row)

    if not grouped:
        raise ValueError("The judgement CSV contains no records.")

    for question_id, rows in grouped.items():
        rows.sort(key=lambda item: item["rank"])
        ranks = [item["rank"] for item in rows]
        if ranks != [1, 2, 3, 4, 5]:
            raise ValueError(
                f"{question_id} must contain exactly ranks 1..5; found {ranks}"
            )
        chunk_ids = [item["chunk_id"] for item in rows]
        if len(chunk_ids) != len(set(chunk_ids)):
            raise ValueError(f"Duplicate chunk_id found for {question_id}")

    return dict(grouped)


def calculate_metrics(grouped: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    total_judged_relevant = sum(
        row["relevance"] for rows in grouped.values() for row in rows
    )
    query_count = len(grouped)
    results: list[dict[str, Any]] = []

    for cutoff in range(1, 6):
        relevant_retrieved = 0
        hit_queries = 0
        reciprocal_ranks: list[float] = []
        relevant_per_query: list[int] = []

        for rows in grouped.values():
            prefix = rows[:cutoff]
            relevant_ranks = [row["rank"] for row in prefix if row["relevance"] == 1]
            count = len(relevant_ranks)
            relevant_retrieved += count
            relevant_per_query.append(count)
            hit_queries += int(count > 0)
            reciprocal_ranks.append(1.0 / relevant_ranks[0] if relevant_ranks else 0.0)

        total_slots = query_count * cutoff
        results.append(
            {
                "cutoff": cutoff,
                "queries": query_count,
                "retrieved_slots": total_slots,
                "relevant_retrieved": relevant_retrieved,
                "irrelevant_retrieved": total_slots - relevant_retrieved,
                "precision_at_k": relevant_retrieved / total_slots,
                "coverage_of_judged_relevant": (
                    relevant_retrieved / total_judged_relevant
                    if total_judged_relevant
                    else 0.0
                ),
                "hit_rate_at_k": hit_queries / query_count,
                "mrr_at_k": mean(reciprocal_ranks),
                "mean_relevant_per_query": mean(relevant_per_query),
            }
        )

    return results


def write_csv(results: list[dict[str, Any]], path: Path) -> None:
    fields = list(results[0].keys())
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)


def write_markdown(
    results: list[dict[str, Any]], grouped: dict[str, list[dict[str, Any]]], path: Path
) -> None:
    total_relevant = sum(
        row["relevance"] for rows in grouped.values() for row in rows
    )
    lines = [
        "# Judged Retrieval Cutoff Analysis",
        "",
        f"- Queries: **{len(grouped)}**",
        f"- Judgements: **{sum(len(rows) for rows in grouped.values())}**",
        f"- Relevant chunks in judged Top-5 pool: **{total_relevant}**",
        "- Label method: **LLM-assisted relevance judgements**",
        "",
        "| Cutoff | Relevant | Irrelevant | Precision@K | Coverage of judged relevant | HitRate@K | MRR@K |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in results:
        lines.append(
            f"| {item['cutoff']} | {item['relevant_retrieved']} | "
            f"{item['irrelevant_retrieved']} | {item['precision_at_k']:.4f} | "
            f"{item['coverage_of_judged_relevant']:.4f} | "
            f"{item['hit_rate_at_k']:.4f} | {item['mrr_at_k']:.4f} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation and limitations",
            "",
            "`Coverage of judged relevant` is the proportion of the relevant chunks "
            "labelled within this Top-5 pool that are retained by a smaller cutoff. "
            "It is **not corpus-level Recall@K**, because relevance outside the "
            "judged Top-5 results has not been exhaustively assessed.",
            "",
            "MRR@K and HitRate@K are 1.0 for all cutoffs in this dataset because "
            "the original rank-1 results were seeded as relevant before the "
            "additional LLM-assisted labelling. Treat these values as descriptive "
            "of the current labels, not as an independent validation of ranking quality.",
            "",
            "The judgement set is small (16 queries across four target documents) "
            "and uses LLM-assisted labels. Audit the seeded rank-1 labels before "
            "using these metrics to select production retrieval settings.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    grouped = load_judgements(CSV_PATH)
    results = calculate_metrics(grouped)
    write_csv(results, METRICS_CSV_PATH)
    write_markdown(results, grouped, REPORT_PATH)

    total = sum(row["relevance"] for rows in grouped.values() for row in rows)
    print("========== RETRIEVAL CUTOFF ANALYSIS ==========")
    print(f"Queries: {len(grouped)}")
    print(f"Judgements: {sum(len(rows) for rows in grouped.values())}")
    print(f"Relevant in judged Top-5 pool: {total}")
    print()
    for item in results:
        print(
            f"Top-{item['cutoff']} | relevant={item['relevant_retrieved']} | "
            f"irrelevant={item['irrelevant_retrieved']} | "
            f"P@{item['cutoff']}={item['precision_at_k']:.4f} | "
            f"judged-relevant-coverage={item['coverage_of_judged_relevant']:.4f} | "
            f"HitRate={item['hit_rate_at_k']:.4f} | MRR={item['mrr_at_k']:.4f}"
        )
    print(f"\nCSV report saved to: {METRICS_CSV_PATH}")
    print(f"Markdown report saved to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
