#!/usr/bin/env python3
"""Create a blinded review pool from the judged top-k retrieval CSV.

The reviewer-facing CSV deliberately omits retrieval rank, source, chunk index,
chunk ID, and all previous relevance labels. A separate answer key is written
under prac_files/ and should not be shared with the reviewer.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_INPUT = PROJECT_ROOT / "prac_files" / "retrieval_judgment_pool_completed.csv"
DEFAULT_AUDIT_OUTPUT = PROJECT_ROOT / "prac_files" / "retrieval_blind_audit.csv"
DEFAULT_KEY_OUTPUT = PROJECT_ROOT / "prac_files" / "retrieval_blind_audit_key.csv"
REQUIRED_COLUMNS = {
    "question_id",
    "question",
    "rank",
    "retrieved_source",
    "chunk_index",
    "chunk_id",
    "content",
    "relevance",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a rank/source/label-blinded relevance audit CSV."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--audit-output", type=Path, default=DEFAULT_AUDIT_OUTPUT)
    parser.add_argument("--key-output", type=Path, default=DEFAULT_KEY_OUTPUT)
    parser.add_argument("--seed", type=int, default=20261104)
    return parser.parse_args()


def make_candidate_id(seed: int, question_id: str, chunk_id: str) -> str:
    token = f"{seed}|{question_id}|{chunk_id}".encode("utf-8")
    digest = hashlib.sha256(token).hexdigest()[:10].upper()
    return f"CAND-{digest}"


def load_rows(path: Path) -> List[Dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(
            f"Input CSV not found: {path}\n"
            "Place retrieval_judgment_pool_completed.csv in prac_files/ "
            "or pass --input with its path."
        )

    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - columns
        if missing:
            raise ValueError(f"Input CSV is missing required columns: {sorted(missing)}")
        rows = list(reader)

    if not rows:
        raise ValueError("Input CSV contains no judgement rows.")

    for line_number, row in enumerate(rows, start=2):
        if not row.get("question_id", "").strip():
            raise ValueError(f"Missing question_id at CSV line {line_number}.")
        if not row.get("question", "").strip():
            raise ValueError(f"Missing question at CSV line {line_number}.")
        if not row.get("content", "").strip():
            raise ValueError(f"Missing chunk content at CSV line {line_number}.")
        if row.get("relevance", "").strip() not in {"0", "1"}:
            raise ValueError(
                f"Expected existing relevance label 0 or 1 at CSV line {line_number}."
            )
        try:
            int(row["rank"])
            int(row["chunk_index"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid rank or chunk_index at CSV line {line_number}.") from exc

    return rows


def write_csv(path: Path, fieldnames: List[str], rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    try:
        rows = load_rows(args.input)
        grouped: Dict[str, List[Dict[str, str]]] = defaultdict(list)
        question_texts: Dict[str, str] = {}

        for row in rows:
            qid = row["question_id"].strip()
            question = row["question"].strip()
            previous_question = question_texts.setdefault(qid, question)
            if previous_question != question:
                raise ValueError(f"Inconsistent question text found for {qid}.")
            grouped[qid].append(row)

        rng = random.Random(args.seed)
        audit_rows: List[Dict[str, str]] = []
        key_rows: List[Dict[str, str]] = []
        seen_candidate_ids = set()

        for qid in sorted(grouped):
            candidates = list(grouped[qid])
            rng.shuffle(candidates)

            for row in candidates:
                candidate_id = make_candidate_id(args.seed, qid, row["chunk_id"])
                if candidate_id in seen_candidate_ids:
                    raise ValueError(
                        "Candidate ID collision detected. Check for duplicate chunk IDs "
                        f"within question {qid}."
                    )
                seen_candidate_ids.add(candidate_id)

                # This file is safe to give to a reviewer: no retrieval metadata
                # or pre-existing relevance labels are included.
                audit_rows.append(
                    {
                        "question_id": qid,
                        "question": question_texts[qid],
                        "candidate_id": candidate_id,
                        "content": row["content"],
                        "relevance": "",
                        "reviewer_notes": "",
                    }
                )

                # Keep this answer key private; it maps blinded candidates back
                # to retrieval metadata and existing labels for later analysis.
                key_rows.append(
                    {
                        "question_id": qid,
                        "candidate_id": candidate_id,
                        "original_rank": row["rank"],
                        "retrieved_source": row["retrieved_source"],
                        "chunk_index": row["chunk_index"],
                        "chunk_id": row["chunk_id"],
                        "previous_relevance": row["relevance"],
                    }
                )

        write_csv(
            args.audit_output,
            ["question_id", "question", "candidate_id", "content", "relevance", "reviewer_notes"],
            audit_rows,
        )
        write_csv(
            args.key_output,
            [
                "question_id",
                "candidate_id",
                "original_rank",
                "retrieved_source",
                "chunk_index",
                "chunk_id",
                "previous_relevance",
            ],
            key_rows,
        )

        print("========== BLINDED RELEVANCE AUDIT ==========")
        print(f"Input rows: {len(rows)}")
        print(f"Questions: {len(grouped)}")
        print(f"Blinded candidates: {len(audit_rows)}")
        print(f"Shuffle seed: {args.seed}")
        print(f"Reviewer file: {args.audit_output.resolve()}")
        print(f"PRIVATE answer key: {args.key_output.resolve()}")
        print("Do not share the answer key with the reviewer.")
        print(
            "Note: rank/source metadata is hidden, but text inside a chunk may "
            "still reveal its document or topic."
        )
        return 0

    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
