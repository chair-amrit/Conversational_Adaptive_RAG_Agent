"""Analyze repeated chunk IDs in the judged retrieval pool.

Expected project layout:
    project_root/
        prac_files/retrieval_judgment_pool_completed.csv
        evaluation/analyze_chunk_repetition.py

Run from the project root:
    py .\\evaluation\\analyze_chunk_repetition.py

The script uses only the Python standard library.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR.parent / "prac_files" / "retrieval_judgment_pool_completed.csv"
JSON_OUTPUT_PATH = BASE_DIR / "chunk_repetition_report.json"
CSV_OUTPUT_PATH = BASE_DIR / "chunk_repetition_by_chunk.csv"
TOP_N = 20

REQUIRED_COLUMNS = {
    "question_id",
    "rank",
    "retrieved_source",
    "chunk_index",
    "chunk_id",
    "content",
    "relevance",
}


def load_judgements(csv_path: Path) -> list[dict[str, Any]]:
    """Load and validate the completed top-k relevance judgement CSV."""
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Judgement CSV not found: {csv_path}\n"
            "Check CSV_PATH and make sure the completed CSV is in prac_files/."
        )

    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV is missing required columns: {sorted(missing)}")

        rows: list[dict[str, Any]] = []
        for line_number, raw in enumerate(reader, start=2):
            chunk_id = (raw.get("chunk_id") or "").strip()
            source = (raw.get("retrieved_source") or "").strip()
            question_id = (raw.get("question_id") or "").strip()

            if not chunk_id or not source or not question_id:
                raise ValueError(
                    f"Missing chunk_id, retrieved_source, or question_id at CSV line {line_number}."
                )

            try:
                rank = int(raw["rank"])
                chunk_index = int(raw["chunk_index"])
                relevance = int(raw["relevance"])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid numeric value at CSV line {line_number}.") from exc

            if relevance not in (0, 1):
                raise ValueError(
                    f"Relevance must be 0 or 1 at CSV line {line_number}; got {relevance}."
                )

            rows.append(
                {
                    "question_id": question_id,
                    "rank": rank,
                    "retrieved_source": source,
                    "chunk_index": chunk_index,
                    "chunk_id": chunk_id,
                    "content": (raw.get("content") or "").strip(),
                    "relevance": relevance,
                }
            )

    if not rows:
        raise ValueError("The judgement CSV contains no data rows.")
    return rows


def build_chunk_statistics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate appearances and relevance labels for each distinct chunk ID."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["chunk_id"]].append(row)

    chunk_stats: list[dict[str, Any]] = []
    for chunk_id, appearances in grouped.items():
        sources = sorted({row["retrieved_source"] for row in appearances})
        if len(sources) != 1:
            raise ValueError(
                f"Chunk ID {chunk_id} is associated with multiple sources: {sources}"
            )

        first = appearances[0]
        relevant_count = sum(row["relevance"] for row in appearances)
        irrelevant_count = len(appearances) - relevant_count
        question_ids = sorted({row["question_id"] for row in appearances})
        preview = " ".join(first["content"].split())[:180]

        chunk_stats.append(
            {
                "chunk_id": chunk_id,
                "retrieved_source": sources[0],
                "chunk_index": first["chunk_index"],
                "appearance_count": len(appearances),
                "distinct_query_count": len(question_ids),
                "question_ids": question_ids,
                "ranks": sorted(row["rank"] for row in appearances),
                "relevant_appearances": relevant_count,
                "irrelevant_appearances": irrelevant_count,
                "relevance_rate": round(relevant_count / len(appearances), 4),
                "content_preview": preview,
            }
        )

    return sorted(
        chunk_stats,
        key=lambda item: (-item["appearance_count"], item["retrieved_source"], item["chunk_index"]),
    )


def build_source_statistics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate retrieval volume and judged relevance by source document."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["retrieved_source"]].append(row)

    total_rows = len(rows)
    total_irrelevant = sum(1 for row in rows if row["relevance"] == 0)
    source_stats: list[dict[str, Any]] = []

    for source, appearances in grouped.items():
        relevant_count = sum(row["relevance"] for row in appearances)
        irrelevant_count = len(appearances) - relevant_count
        source_stats.append(
            {
                "source": source,
                "retrieval_appearances": len(appearances),
                "unique_chunk_ids": len({row["chunk_id"] for row in appearances}),
                "distinct_queries": len({row["question_id"] for row in appearances}),
                "relevant_appearances": relevant_count,
                "irrelevant_appearances": irrelevant_count,
                "retrieval_appearance_share": round(len(appearances) / total_rows, 4),
                "share_of_all_irrelevant_appearances": (
                    round(irrelevant_count / total_irrelevant, 4)
                    if total_irrelevant
                    else 0.0
                ),
            }
        )

    return sorted(
        source_stats,
        key=lambda item: (-item["retrieval_appearances"], item["source"]),
    )


def write_chunk_csv(path: Path, chunk_stats: list[dict[str, Any]]) -> None:
    fieldnames = [
        "chunk_id",
        "retrieved_source",
        "chunk_index",
        "appearance_count",
        "distinct_query_count",
        "question_ids",
        "ranks",
        "relevant_appearances",
        "irrelevant_appearances",
        "relevance_rate",
        "content_preview",
    ]

    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for item in chunk_stats:
            row = item.copy()
            row["question_ids"] = ";".join(row["question_ids"])
            row["ranks"] = ";".join(str(rank) for rank in row["ranks"])
            writer.writerow(row)


def main() -> None:
    rows = load_judgements(CSV_PATH)
    chunk_stats = build_chunk_statistics(rows)
    source_stats = build_source_statistics(rows)

    unique_chunk_count = len(chunk_stats)
    repeated_chunks = [item for item in chunk_stats if item["appearance_count"] > 1]
    repeated_appearances = sum(item["appearance_count"] for item in repeated_chunks)
    irrelevant_count = sum(1 for row in rows if row["relevance"] == 0)
    top_three_sources = source_stats[:3]

    report = {
        "evaluation": "chunk_repetition_diagnostics_v1",
        "input_csv": str(CSV_PATH),
        "summary": {
            "total_retrieval_appearances": len(rows),
            "unique_chunk_ids": unique_chunk_count,
            "repeated_chunk_ids": len(repeated_chunks),
            "appearances_from_repeated_chunks": repeated_appearances,
            "repeated_appearance_rate": round(repeated_appearances / len(rows), 4),
            "irrelevant_appearances": irrelevant_count,
            "top_3_source_appearances": sum(
                item["retrieval_appearances"] for item in top_three_sources
            ),
            "top_3_source_appearance_share": round(
                sum(item["retrieval_appearances"] for item in top_three_sources) / len(rows),
                4,
            ),
            "top_3_source_irrelevant_appearances": sum(
                item["irrelevant_appearances"] for item in top_three_sources
            ),
        },
        "source_statistics": source_stats,
        "repeated_chunks": repeated_chunks,
        "most_repeated_chunks": repeated_chunks[:TOP_N],
    }

    JSON_OUTPUT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    write_chunk_csv(CSV_OUTPUT_PATH, chunk_stats)

    summary = report["summary"]
    print("========== CHUNK REPETITION SUMMARY ==========")
    print(f"Total retrieval appearances: {summary['total_retrieval_appearances']}")
    print(f"Unique chunk IDs: {summary['unique_chunk_ids']}")
    print(f"Repeated chunk IDs: {summary['repeated_chunk_ids']}")
    print(
        "Appearances from repeated chunks: "
        f"{summary['appearances_from_repeated_chunks']} "
        f"({summary['repeated_appearance_rate']:.1%})"
    )
    print(
        "Top 3 sources' retrieval appearances: "
        f"{summary['top_3_source_appearances']} "
        f"({summary['top_3_source_appearance_share']:.1%})"
    )
    print(
        "Top 3 sources' irrelevant appearances: "
        f"{summary['top_3_source_irrelevant_appearances']} / {irrelevant_count}"
    )

    print("\nMost repeated chunks:")
    for item in repeated_chunks[:TOP_N]:
        print(
            f"{item['retrieved_source']} | chunk {item['chunk_index']} | "
            f"appearances={item['appearance_count']} | "
            f"relevant={item['relevant_appearances']} | "
            f"irrelevant={item['irrelevant_appearances']} | "
            f"queries={','.join(item['question_ids'])}"
        )

    print(f"\nJSON report saved to: {JSON_OUTPUT_PATH}")
    print(f"Per-chunk CSV saved to: {CSV_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
