# Source-Level Retrieval Concentration Report

> Scope: the judged top-k retrieval pool only. These counts do not represent all chunks stored for each document.

## Overall summary

- Retrieval appearances: **80**
- Distinct retrieved chunk IDs: **36**
- Sources represented: **8**
- Relevant appearances: **19**
- Irrelevant appearances: **61**
- Chunk IDs repeated across appearances: **20**
- Top 3 sources account for **51/80** appearances (63.7%) and **36/61** irrelevant appearances (59.0%).

## Source breakdown

| Source | Appearances | Unique retrieved chunks | Queries | Relevant | Irrelevant | Relevance rate | Share of irrelevant | Repeated chunk IDs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| rag_service_design.html | 20 | 5 | 7 | 5 | 15 | 25.0% | 24.6% | 5 |
| quant_strategy_spec.json | 17 | 5 | 5 | 6 | 11 | 35.3% | 18.0% | 5 |
| project_atlas_kickoff.pptx | 14 | 5 | 4 | 4 | 10 | 28.6% | 16.4% | 4 |
| dabstep_task_registry.xlsx | 9 | 4 | 4 | 4 | 5 | 44.4% | 8.2% | 3 |
| min_project.pdf | 9 | 8 | 6 | 0 | 9 | 0.0% | 14.8% | 1 |
| notes.txt | 8 | 7 | 5 | 0 | 8 | 0.0% | 13.1% | 1 |
| sample.docx | 2 | 1 | 2 | 0 | 2 | 0.0% | 3.3% | 1 |
| finetune.pdf | 1 | 1 | 1 | 0 | 1 | 0.0% | 1.6% | 0 |

## Interpretation notes

- `Appearances` counts query-chunk retrieval rows, so the same chunk can contribute multiple times.
- `Unique retrieved chunks` counts distinct chunk IDs observed for that source in this pool, not the total number of chunks in the vector store.
- `Relevance rate` is the fraction of this source's appearances labelled relevant; it is not a source-wide quality score.
- `Share of irrelevant` measures how much this source contributes to the 61 (or current total) irrelevant rows in this pool.
- `Repeated chunk IDs` counts chunks appearing in more than one query result for the source.
- A document can have many irrelevant appearances because it is frequently retrieved, because a few chunks repeat, or both. Inspect chunk-level results before changing ingestion or retrieval settings.
