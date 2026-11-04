"""Analyze source-level retrieval concentration in a judged top-k pool.

Expected project layout:
    project_root/
        prac_files/retrieval_judgment_pool_completed.csv
        evaluation/analyze_source_concentration.py

Run from the project root:
    py .\\evaluation\\analyze_source_concentration.py

Outputs are written to evaluation/:
    source_concentration_report.csv
    source_concentration_report.md

This script uses only the Python standard library. Counts describe the judged
retrieval pool, not the full vector-store corpus.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR.parent / "prac_files" / "retrieval_judgment_pool_completed.csv"
CSV_OUTPUT_PATH = BASE_DIR / "source_concentration_report.csv"
MARKDOWN_OUTPUT_PATH = BASE_DIR / "source_concentration_report.md"

REQUIRED_COLUMNS = {
    "question_id",
    "expected_source",
    "rank",
    "retrieved_source",
    "chunk_id",
    "relevance",
}


def load_judgements(csv_path: Path) -> list[dict[str, Any]]:
    """Load and validate the completed judgement pool."""
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Judgement CSV not found: {csv_path}\n"
            "Make sure retrieval_judgment_pool_completed.csv is in prac_files/."
        )

    rows: list[dict[str, Any]] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV is missing required columns: {sorted(missing)}")

        for line_number, raw in enumerate(reader, start=2):
            question_id = (raw.get("question_id") or "").strip()
            expected_source = (raw.get("expected_source") or "").strip()
            retrieved_source = (raw.get("retrieved_source") or "").strip()
            chunk_id = (raw.get("chunk_id") or "").strip()

            if not all((question_id, expected_source, retrieved_source, chunk_id)):
                raise ValueError(
                    "Missing question_id, expected_source, retrieved_source, "
                    f"or chunk_id at CSV line {line_number}."
                )

            try:
                rank = int(raw["rank"])
                relevance = int(raw["relevance"])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid numeric value at CSV line {line_number}.") from exc

            if rank < 1:
                raise ValueError(f"Rank must be >= 1 at CSV line {line_number}.")
            if relevance not in (0, 1):
                raise ValueError(
                    f"Relevance must be 0 or 1 at CSV line {line_number}; got {relevance}."
                )

            rows.append(
                {
                    "question_id": question_id,
                    "expected_source": expected_source,
                    "rank": rank,
                    "retrieved_source": retrieved_source,
                    "chunk_id": chunk_id,
                    "relevance": relevance,
                }
            )

    if not rows:
        raise ValueError("The judgement CSV contains no data rows.")
    return rows


def build_source_statistics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate source volume, relevance, and repetition within this pool."""
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_source[row["retrieved_source"]].append(row)

    total_appearances = len(rows)
    total_irrelevant = sum(row["relevance"] == 0 for row in rows)
    stats: list[dict[str, Any]] = []

    for source, appearances in by_source.items():
        by_chunk: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in appearances:
            by_chunk[row["chunk_id"]].append(row)

        relevant = sum(row["relevance"] for row in appearances)
        irrelevant = len(appearances) - relevant
        repeated_chunks = [items for items in by_chunk.values() if len(items) > 1]
        repeated_appearances = sum(len(items) for items in repeated_chunks)
        expected_source_appearances = sum(
            row["retrieved_source"] == row["expected_source"] for row in appearances
        )
        cross_document_irrelevant = sum(
            row["retrieved_source"] != row["expected_source"] and row["relevance"] == 0
            for row in appearances
        )

        stats.append(
            {
                "source": source,
                "retrieval_appearances": len(appearances),
                "unique_retrieved_chunks": len(by_chunk),
                "distinct_queries": len({row["question_id"] for row in appearances}),
                "relevant_appearances": relevant,
                "irrelevant_appearances": irrelevant,
                "judged_relevance_rate": relevant / len(appearances),
                "retrieval_appearance_share": len(appearances) / total_appearances,
                "share_of_all_irrelevant": (
                    irrelevant / total_irrelevant if total_irrelevant else 0.0
                ),
                "repeated_chunk_ids": len(repeated_chunks),
                "appearances_from_repeated_chunks": repeated_appearances,
                "expected_source_appearances": expected_source_appearances,
                "cross_document_appearances": len(appearances) - expected_source_appearances,
                "cross_document_irrelevant_appearances": cross_document_irrelevant,
            }
        )

    return sorted(stats, key=lambda item: (-item["retrieval_appearances"], item["source"]))


def write_csv(path: Path, stats: list[dict[str, Any]]) -> None:
    fieldnames = list(stats[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for item in stats:
            row = item.copy()
            for key in (
                "judged_relevance_rate",
                "retrieval_appearance_share",
                "share_of_all_irrelevant",
            ):
                row[key] = f"{row[key]:.4f}"
            writer.writerow(row)


def write_markdown(path: Path, rows: list[dict[str, Any]], stats: list[dict[str, Any]]) -> None:
    total = len(rows)
    relevant = sum(row["relevance"] for row in rows)
    irrelevant = total - relevant
    unique_chunks = len({row["chunk_id"] for row in rows})
    repeated_chunk_ids = sum(
        1
        for count in _chunk_appearance_counts(rows).values()
        if count > 1
    )
    top_three = stats[:3]
    top_three_appearances = sum(item["retrieval_appearances"] for item in top_three)
    top_three_irrelevant = sum(item["irrelevant_appearances"] for item in top_three)
    top_three_irrelevant_share = (
        top_three_irrelevant / irrelevant if irrelevant else 0.0
    )

    lines = [
        "# Source-Level Retrieval Concentration Report",
        "",
        "> Scope: the judged top-k retrieval pool only. These counts do not represent all chunks stored for each document.",
        "",
        "## Overall summary",
        "",
        f"- Retrieval appearances: **{total}**",
        f"- Distinct retrieved chunk IDs: **{unique_chunks}**",
        f"- Sources represented: **{len(stats)}**",
        f"- Relevant appearances: **{relevant}**",
        f"- Irrelevant appearances: **{irrelevant}**",
        f"- Chunk IDs repeated across appearances: **{repeated_chunk_ids}**",
        f"- Top 3 sources account for **{top_three_appearances}/{total}** appearances ({top_three_appearances / total:.1%}) and **{top_three_irrelevant}/{irrelevant}** irrelevant appearances ({top_three_irrelevant_share:.1%}).",
        "",
        "## Source breakdown",
        "",
        "| Source | Appearances | Unique retrieved chunks | Queries | Relevant | Irrelevant | Relevance rate | Share of irrelevant | Repeated chunk IDs |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for item in stats:
        lines.append(
            "| {source} | {appearances} | {unique} | {queries} | {relevant} | {irrelevant} | {rate:.1%} | {irrelevant_share:.1%} | {repeated} |".format(
                source=item["source"],
                appearances=item["retrieval_appearances"],
                unique=item["unique_retrieved_chunks"],
                queries=item["distinct_queries"],
                relevant=item["relevant_appearances"],
                irrelevant=item["irrelevant_appearances"],
                rate=item["judged_relevance_rate"],
                irrelevant_share=item["share_of_all_irrelevant"],
                repeated=item["repeated_chunk_ids"],
            )
        )

    lines.extend(
        [
            "",
            "## Interpretation notes",
            "",
            "- `Appearances` counts query-chunk retrieval rows, so the same chunk can contribute multiple times.",
            "- `Unique retrieved chunks` counts distinct chunk IDs observed for that source in this pool, not the total number of chunks in the vector store.",
            "- `Relevance rate` is the fraction of this source's appearances labelled relevant; it is not a source-wide quality score.",
            "- `Share of irrelevant` measures how much this source contributes to the 61 (or current total) irrelevant rows in this pool.",
            "- `Repeated chunk IDs` counts chunks appearing in more than one query result for the source.",
            "- A document can have many irrelevant appearances because it is frequently retrieved, because a few chunks repeat, or both. Inspect chunk-level results before changing ingestion or retrieval settings.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _chunk_appearance_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        counts[row["chunk_id"]] += 1
    return counts


def main() -> None:
    rows = load_judgements(CSV_PATH)
    stats = build_source_statistics(rows)
    write_csv(CSV_OUTPUT_PATH, stats)
    write_markdown(MARKDOWN_OUTPUT_PATH, rows, stats)

    total = len(rows)
    relevant = sum(row["relevance"] for row in rows)
    irrelevant = total - relevant
    print("========== SOURCE CONCENTRATION SUMMARY ==========")
    print(f"Retrieval appearances: {total}")
    print(f"Relevant / irrelevant: {relevant} / {irrelevant}")
    print(f"Sources represented: {len(stats)}")
    print("\nSource breakdown (sorted by retrieval appearances):")
    for item in stats:
        print(
            f"{item['source']} | appearances={item['retrieval_appearances']} "
            f"| unique_chunks={item['unique_retrieved_chunks']} "
            f"| relevant={item['relevant_appearances']} "
            f"| irrelevant={item['irrelevant_appearances']} "
            f"| relevance_rate={item['judged_relevance_rate']:.1%} "
            f"| irrelevant_share={item['share_of_all_irrelevant']:.1%}"
        )

    print(f"\nCSV report saved to: {CSV_OUTPUT_PATH}")
    print(f"Markdown report saved to: {MARKDOWN_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
