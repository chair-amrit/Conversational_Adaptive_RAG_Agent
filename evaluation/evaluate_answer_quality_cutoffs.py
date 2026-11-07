"""Run a paired Top-3 vs Top-5 answer-quality experiment.

Retrieves the Top-5 once per question and supplies the same ranked prefix to
both conditions. Generation uses the production ``generate_chain`` prompt and
model. The script writes a provenance-rich JSON artifact and a human-review CSV.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langchain_chroma import Chroma
from langchain_core.load.dump import dumpd

from llm_utils import generate_chain
from rag_utils import GoogleGenerativeAIEmbeddings


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DATASET_PATH = BASE_DIR / "retrieval_eval_dataset.json"
AUDIT_PATH = PROJECT_ROOT / "prac_files" / "retrieval_blind_audit.csv"
AUDIT_KEY_PATH = PROJECT_ROOT / "prac_files" / "retrieval_blind_audit_key.csv"
COLLECTION_NAME = "my_rag_multiformat"
PERSIST_DIR = PROJECT_ROOT / "chroma_db"
EMBEDDING_MODEL = "models/gemini-embedding-001"
GENERATION_MODEL = "gemini-3.5-flash-lite"
CUTOFFS = (3, 5)
REVIEW_FIELDS = [
    "response_id",
    "question_id",
    "question",
    "answer",
    "correctness_0_1_2",
    "completeness_0_1_2",
    "citation_support_0_1_2",
    "reviewer_notes",
    "evidence_or_source_checked",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        help=(
            "Output directory. Defaults to a UTC timestamped directory under "
            "evaluation/answer_quality_runs/. Use a new directory per run."
        ),
    )
    return parser.parse_args()


def load_dataset(path: Path = DATASET_PATH) -> dict[str, Any]:
    dataset = json.loads(path.read_text(encoding="utf-8-sig"))
    cases = dataset.get("test_cases")
    if not isinstance(cases, list) or len(cases) != 16:
        raise ValueError("Expected exactly 16 evaluation questions in the dataset.")
    ids = [case.get("id") for case in cases]
    if ids != [f"Q{i:02d}" for i in range(1, 17)]:
        raise ValueError("Expected questions Q01 through Q16 in their stored order.")
    for case in cases:
        if not case.get("question", "").strip() or not case.get("relevant_chunk_ids"):
            raise ValueError(f"Question {case.get('id')} is missing required fields.")
    return dataset


def load_audit_labels(
    audit_path: Path = AUDIT_PATH, key_path: Path = AUDIT_KEY_PATH
) -> dict[tuple[str, str], dict[str, Any]]:
    """Join reviewer labels to chunk IDs without assuming retrieval rank is stable."""
    with audit_path.open("r", encoding="utf-8-sig", newline="") as handle:
        audit_rows = list(csv.DictReader(handle))
    with key_path.open("r", encoding="utf-8-sig", newline="") as handle:
        key_rows = list(csv.DictReader(handle))

    labels_by_candidate: dict[tuple[str, str], dict[str, Any]] = {}
    for line_number, row in enumerate(audit_rows, start=2):
        qid = (row.get("question_id") or "").strip()
        candidate_id = (row.get("candidate_id") or "").strip()
        label = (row.get("relevance") or "").strip()
        if not qid or not candidate_id or label not in {"0", "1"}:
            raise ValueError(f"Incomplete or invalid blinded audit row at line {line_number}.")
        key = (qid, candidate_id)
        if key in labels_by_candidate:
            raise ValueError(f"Duplicate blinded audit candidate: {key}")
        labels_by_candidate[key] = {
            "relevance": int(label),
            "reviewer_notes": (row.get("reviewer_notes") or "").strip(),
        }

    by_chunk: dict[tuple[str, str], dict[str, Any]] = {}
    for line_number, row in enumerate(key_rows, start=2):
        qid = (row.get("question_id") or "").strip()
        candidate_id = (row.get("candidate_id") or "").strip()
        chunk_id = (row.get("chunk_id") or "").strip()
        label = labels_by_candidate.get((qid, candidate_id))
        if not qid or not chunk_id or label is None:
            raise ValueError(f"Invalid or unmatched blinded audit key row at line {line_number}.")
        key = (qid, chunk_id)
        if key in by_chunk:
            raise ValueError(f"Duplicate audited chunk for question: {key}")
        by_chunk[key] = label

    if len(by_chunk) != 80:
        raise ValueError(f"Expected 80 completed blinded judgements; found {len(by_chunk)}.")
    return by_chunk


def validate_gold_ids(db: Chroma, cases: list[dict[str, Any]]) -> None:
    ids = list(dict.fromkeys(
        chunk_id for case in cases for chunk_id in case["relevant_chunk_ids"]
    ))
    stored = db.get(ids=ids, include=["metadatas"])
    missing = set(ids) - set(stored["ids"])
    if missing:
        raise ValueError(f"Evaluation gold chunk IDs missing from Chroma: {sorted(missing)}")
    metadata_by_id = dict(zip(stored["ids"], stored["metadatas"]))
    for case in cases:
        for chunk_id in case["relevant_chunk_ids"]:
            actual = metadata_by_id[chunk_id].get("file_name")
            if actual != case["source_file"]:
                raise ValueError(
                    f"{case['id']} expects {case['source_file']} for {chunk_id}, found {actual}."
                )


def corpus_fingerprint(db: Chroma) -> tuple[int, str]:
    records = db.get(include=["documents", "metadatas"])
    canonical = [
        {"id": chunk_id, "document": document, "metadata": metadata}
        for chunk_id, document, metadata in sorted(
            zip(records["ids"], records["documents"], records["metadatas"]),
            key=lambda row: row[0],
        )
    ]
    serialized = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return len(canonical), hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def format_context(chunks: list[dict[str, Any]]) -> str:
    """Mirror main.py's document context format so generation uses production evidence."""
    parts = []
    for chunk in chunks:
        metadata = chunk["metadata"]
        source = metadata.get("file_name")
        if not source:
            source = Path(metadata.get("source", "Unknown source")).name
        page = metadata.get("page")
        if page is not None:
            try:
                page_label = f"Page {int(page) + 1}"
            except (ValueError, TypeError):
                page_label = f"Page {page}"
        else:
            page_label = "Page unknown"
        parts.append(
            f"Source: {source}\n{page_label}\nContent:\n{chunk['content']}"
        )
    return "\n\n---\n\n".join(parts)


def response_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(part for part in parts if part).strip()
    return str(content) if content is not None else ""


def summarize_context_metrics(results: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    top5_relevant_total = sum(
        chunk["relevance_label"] == 1
        for result in results
        for chunk in result["conditions"]["top5"]["retrieved_chunks"]
        if chunk["relevance_label"] is not None
    )
    for cutoff in CUTOFFS:
        key = f"top{cutoff}"
        chunks = [
            chunk
            for result in results
            for chunk in result["conditions"][key]["retrieved_chunks"]
        ]
        relevant = sum(chunk["relevance_label"] == 1 for chunk in chunks)
        irrelevant = sum(chunk["relevance_label"] == 0 for chunk in chunks)
        unjudged = sum(chunk["relevance_label"] is None for chunk in chunks)
        summary[key] = {
            "questions": len(results),
            "retrieved_chunks": len(chunks),
            "reviewer_labeled_relevant_chunks": relevant,
            "reviewer_labeled_irrelevant_chunks": irrelevant,
            "unjudged_chunks": unjudged,
            "relevance_rate_among_labeled_chunks": (
                relevant / (relevant + irrelevant) if relevant + irrelevant else None
            ),
            "mean_context_characters": round(mean_or_zero(
                len(result["conditions"][key]["context"]) for result in results
            ), 2),
            "mean_distinct_sources": round(mean_or_zero(
                len({chunk["metadata"].get("file_name") for chunk in result["conditions"][key]["retrieved_chunks"]})
                for result in results
            ), 2),
            "share_of_reviewer_labeled_relevant_top5_chunks_retained": (
                relevant / top5_relevant_total if top5_relevant_total else None
            ),
        }
    return summary


def mean_or_zero(values: Any) -> float:
    items = list(values)
    return sum(items) / len(items) if items else 0.0


def prompt_fingerprint(prompt: Any) -> str:
    """Hash LangChain's serialized prompt templates and their configuration."""
    representation = {
        "serialized_prompt": dumpd(prompt),
        "configuration": {
            "name": prompt.name,
            "input_variables": prompt.input_variables,
            "optional_variables": prompt.optional_variables,
            "partial_variables": prompt.partial_variables,
            "validate_template": prompt.validate_template,
            "metadata": prompt.metadata,
            "tags": prompt.tags,
        },
    }
    canonical_json = json.dumps(
        representation,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def build_review_rows(results: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = []
    key_rows = []
    for result in results:
        for cutoff in CUTOFFS:
            condition = result["conditions"][f"top{cutoff}"]
            response_id = "ANS-" + hashlib.sha256(
                f"{result['question_id']}|top{cutoff}".encode("utf-8")
            ).hexdigest()[:10].upper()
            rows.append({
                "response_id": response_id,
                "question_id": result["question_id"],
                "question": result["question"],
                "answer": condition["answer"],
                "correctness_0_1_2": "",
                "completeness_0_1_2": "",
                "citation_support_0_1_2": "",
                "reviewer_notes": "",
                "evidence_or_source_checked": "",
            })
            key_rows.append({
                "response_id": response_id,
                "question_id": result["question_id"],
                "cutoff": cutoff,
            })
    # Keep paired answers apart in the reviewer-facing file and hide the cutoff.
    random.Random(20261106).shuffle(rows)
    return rows, key_rows


def write_outputs(output_dir: Path, artifact: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "results.json"
    temporary_path = output_dir / "results.json.tmp"
    temporary_path.write_text(
        json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary_path.replace(json_path)
    review_rows, key_rows = build_review_rows(artifact["results"])
    with (output_dir / "human_review.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(review_rows)
    with (output_dir / "answer_key.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["response_id", "question_id", "cutoff"])
        writer.writeheader()
        writer.writerows(key_rows)


def run(output_dir: Path) -> dict[str, Any]:
    dataset = load_dataset()
    cases = dataset["test_cases"]
    audit_labels = load_audit_labels()
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
    db = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=str(PERSIST_DIR),
        embedding_function=embeddings,
    )
    validate_gold_ids(db, cases)
    corpus_size, corpus_sha256 = corpus_fingerprint(db)
    chain = generate_chain()
    prompt_sha256 = prompt_fingerprint(chain.steps[0])
    artifact: dict[str, Any] = {
        "experiment": "answer_quality_top3_vs_top5_v1",
        "status": "running",
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_name": dataset["dataset_name"],
        "dataset_sha256": hashlib.sha256(DATASET_PATH.read_bytes()).hexdigest(),
        "question_count": len(cases),
        "collection_name": COLLECTION_NAME,
        "corpus_record_count": corpus_size,
        "corpus_sha256": corpus_sha256,
        "embedding_model": EMBEDDING_MODEL,
        "generation_model": GENERATION_MODEL,
        "generation_temperature": "provider default; matches current production chain configuration",
        "production_retriever_k": 10,
        "experiment_retrieval_k": 5,
        "cutoffs": list(CUTOFFS),
        "generation_prompt_sha256": prompt_sha256,
        "retrieval_label_source": {
            "file": "prac_files/retrieval_blind_audit.csv plus private answer key",
            "method": "completed blinded reviewer labels joined by question_id and chunk_id",
            "labels_available": len(audit_labels),
            "unmatched_new_chunks": "marked unjudged; never assumed irrelevant",
        },
        "evaluation_rubric": "docs/answer-quality-cutoff-experiment.md",
        "results": [],
    }
    write_outputs(output_dir, artifact)

    query_vectors = [embeddings.embed_query(case["question"]) for case in cases]
    retrieved = db._collection.query(
        query_embeddings=query_vectors,
        n_results=5,
        include=["documents", "metadatas", "distances"],
    )
    generation_order_rng = random.Random(20261106)
    for index, case in enumerate(cases):
        chunk_records = []
        for rank, chunk_id in enumerate(retrieved["ids"][index], start=1):
            metadata = retrieved["metadatas"][index][rank - 1] or {}
            label = audit_labels.get((case["id"], chunk_id))
            chunk_records.append({
                "rank": rank,
                "chunk_id": chunk_id,
                "distance": retrieved["distances"][index][rank - 1],
                "metadata": metadata,
                "content": retrieved["documents"][index][rank - 1],
                "relevance_label": label["relevance"] if label else None,
                "reviewer_notes": label["reviewer_notes"] if label else None,
            })
        if len(chunk_records) != 5:
            raise ValueError(f"{case['id']} returned {len(chunk_records)} chunks, expected 5.")

        result = {
            "question_id": case["id"],
            "question": case["question"],
            "expected_source_from_dataset": case["source_file"],
            "ground_truth_chunk_ids_from_dataset": case["relevant_chunk_ids"],
            "generation_order": [],
            "conditions": {},
        }
        order = list(CUTOFFS)
        generation_order_rng.shuffle(order)
        result["generation_order"] = [f"top{cutoff}" for cutoff in order]
        for cutoff in order:
            prefix = chunk_records[:cutoff]
            context = format_context(prefix)
            response = chain.invoke({
                "messages": [],
                "context": context,
                "question": case["question"],
            })
            result["conditions"][f"top{cutoff}"] = {
                "retrieved_chunks": prefix,
                "context": context,
                "context_characters": len(context),
                "answer": response_to_text(response.content),
                "human_scores": None,
            }
        artifact["results"].append(result)
        artifact["context_metrics"] = summarize_context_metrics(artifact["results"])
        artifact["progress"] = f"{len(artifact['results'])}/{len(cases)} questions complete"
        write_outputs(output_dir, artifact)
        print(f"{case['id']} generated at Top-3 and Top-5")

    artifact["status"] = "complete"
    artifact["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    artifact.pop("progress", None)
    artifact["context_metrics"] = summarize_context_metrics(artifact["results"])
    write_outputs(output_dir, artifact)
    print(f"JSON results: {output_dir / 'results.json'}")
    print(f"Human review: {output_dir / 'human_review.csv'}")
    return artifact


def main() -> int:
    args = parse_args()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = args.output_dir or BASE_DIR / "answer_quality_runs" / run_id
    try:
        artifact = run(output_dir.resolve())
        for cutoff, values in artifact["context_metrics"].items():
            print(
                f"{cutoff}: relevant={values['reviewer_labeled_relevant_chunks']}, "
                f"irrelevant={values['reviewer_labeled_irrelevant_chunks']}, "
                f"unjudged={values['unjudged_chunks']}, "
                f"mean_context_chars={values['mean_context_characters']}"
            )
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
