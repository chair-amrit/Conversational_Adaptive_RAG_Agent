# Retrieval Failure Analysis — Judged Top-5 Pool

## Scope

This analysis uses 16 evaluation questions and the 80 query–chunk pairs retrieved in the existing Top-5 judgement pool. The pool covers four target documents; retrieved chunks from other corpus documents are included as potential false positives for these questions. Counts describe this evaluation pool only, not the full Chroma collection.

The relevance labels were LLM-assisted. The original rank-1 positive labels were seeded before the additional judgement pass, so rank-sensitive metrics must be interpreted with that limitation.

## Judged baseline

- Queries: 16
- Judgements: 80
- Labelled relevant: 19
- Labelled irrelevant: 61
- Precision@5: 0.2375
- MRR@5: 1.0
- HitRate@5: 1.0

MRR@5 and HitRate@5 equal 1.0 because every query's rank-1 result had already been seeded as relevant. These values are correct for the current labels but are not independent evidence that the retriever's first result is always relevant.

## Retrieval concentration

| Source | Appearances | Unique retrieved chunks | Relevant | Irrelevant |
|---|---:|---:|---:|---:|
| `rag_service_design.html` | 20 | 5 | 5 | 15 |
| `quant_strategy_spec.json` | 17 | 5 | 6 | 11 |
| `project_atlas_kickoff.pptx` | 14 | 5 | 4 | 10 |
| `dabstep_task_registry.xlsx` | 9 | 4 | 4 | 5 |
| `min_project.pdf` | 9 | 8 | 0 | 9 |
| `notes.txt` | 8 | 7 | 0 | 8 |
| `sample.docx` | 2 | 1 | 0 | 2 |
| `finetune.pdf` | 1 | 1 | 0 | 1 |

The top three sources account for 51/80 (63.75%) of appearances and 36/61 (59.0%) of irrelevant appearances. The distinct chunk counts are the number observed in this judgement pool, not the total chunk count per document in Chroma.

The three small target documents each contribute five distinct chunks to this pool, and their chunks recur across multiple questions. However, document size alone is not a sufficient explanation: `min_project.pdf` and `notes.txt` also contribute 17 irrelevant appearances combined. The next diagnosis should inspect repeated chunk content and question similarity rather than assume small files are the sole cause.

## Repeated chunks

- Retrieval appearances: 80
- Distinct chunk IDs: 36
- Chunk IDs appearing in more than one query: 20
- Appearances contributed by those repeated IDs: 64 (80%)

Examples of repeated chunks with weak relevance in this pool:

- `rag_service_design.html`, chunk index 3: 5 appearances, 0 relevant, 5 irrelevant.
- `quant_strategy_spec.json`, chunk index 3: 5 appearances, 1 relevant, 4 irrelevant.
- `project_atlas_kickoff.pptx`, chunk index 3: 4 appearances, 1 relevant, 3 irrelevant.

These are inspection candidates, not confirmed causes. Their content should be reviewed alongside the exact queries before modifying chunking or embeddings.

## Cutoff analysis

| Cutoff | Relevant | Irrelevant | Precision@K | Coverage of the 19 judged-relevant chunks |
|---:|---:|---:|---:|---:|
| Top 1 | 16 | 0 | 1.0000 | 0.8421 |
| Top 2 | 18 | 14 | 0.5625 | 0.9474 |
| Top 3 | 19 | 29 | 0.3958 | 1.0000 |
| Top 4 | 19 | 45 | 0.2969 | 1.0000 |
| Top 5 | 19 | 61 | 0.2375 | 1.0000 |

Coverage here means the share of relevant chunks already labelled within this Top-5 pool retained by the cutoff. It is not corpus-level Recall@K because relevance outside the judged pool has not been exhaustively assessed.

Top 3 retains all 19 labelled relevant chunks in this pool while excluding 32 labelled-irrelevant chunks relative to Top 5. This makes Top 3 a candidate for a controlled experiment, not an approved production change.

## Next validation step: blinded relevance audit

Before relying on rank-sensitive metrics or changing retrieval settings, independently re-review the 80 candidates:

1. Generate `retrieval_blind_audit.csv` with `evaluation/generate_blinded_relevance_audit.py`.
2. Give the reviewer-facing CSV to a reviewer without sharing `retrieval_blind_audit_key.csv`.
3. Ask the reviewer to judge whether each chunk directly helps answer its question. Use `1` for relevant and `0` for irrelevant, and record a short reason for borderline cases.
4. Preserve the private answer key. Join the new labels back by `(question_id, candidate_id)` only after the blind review is complete.
5. Recompute the cutoff metrics from the independently reviewed labels before selecting a production `k`.

The process hides retrieval rank, retrieved source, chunk index, chunk ID, and previous labels from the reviewer. The chunk text itself may still reveal its source or topic; this is a metadata-blinded audit, not a guarantee of perfect anonymity.

## Decision

Do not change production `top_k`, chunk size, overlap, embedding model, or add reranking based only on this pool. Complete the blind audit first, then run a controlled before/after evaluation on the same questions and labels.
