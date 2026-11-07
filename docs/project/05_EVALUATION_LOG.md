# Retrieval and Answer Evaluation Log

## Evaluation E001 — Initial retrieval baseline

**Dataset:** 16 questions  
**Target documents:** 4  
**Initial retrieval cutoff:** Top 10

Initial metrics:
- Precision@10: 0.1063
- Recall@10: 1.0000
- MRR@10: 1.0000

**Limitation:** Initial relevance labels covered only selected gold chunks. Unlabelled chunks could not automatically be considered irrelevant.

## Evaluation E002 — Judged Top-5 retrieval

**Dataset:** 16 questions  
**Judgements:** 80  
**Relevant:** 19  
**Irrelevant:** 61  
**Judgement method:** LLM-assisted, followed by independent review.

Results:

| Metric | Result |
|---|---:|
| Precision@5 | 0.2375 |
| MRR@5 | 1.0000 |
| HitRate@5 | 1.0000 |

## Evaluation E003 — Retrieval concentration

Results:
- Total retrieval appearances: 80.
- Distinct chunk IDs: 36.
- Repeated chunk IDs: 20.
- Appearances from repeated chunks: 64.
- Top three sources' appearances: 51.
- Top three sources' irrelevant appearances: 36.

Observation: A small set of chunks appears repeatedly across different questions.

## Evaluation E004 — Source-level analysis

| Source | Appearances | Unique chunks | Irrelevant |
|---|---:|---:|---:|
| rag_service_design.html | 20 | 5 | 15 |
| quant_strategy_spec.json | 17 | 5 | 11 |
| project_atlas_kickoff.pptx | 14 | 5 | 10 |
| dabstep_task_registry.xlsx | 9 | 4 | 5 |
| min_project.pdf | 9 | 8 | 9 |
| notes.txt | 8 | 7 | 8 |
| sample.docx | 2 | 1 | 2 |
| finetune.pdf | 1 | 1 | 1 |

## Evaluation E005 — Top-K cutoff analysis

| Cutoff | Precision | Relevant candidates retained |
|---|---:|---:|
| Top 1 | 1.0000 | 16/19 |
| Top 2 | 0.5625 | 18/19 |
| Top 3 | 0.3958 | 19/19 |
| Top 4 | 0.2969 | 19/19 |
| Top 5 | 0.2375 | 19/19 |

These are results from the judged Top-5 pool. The retained-candidate fraction is not corpus-level Recall@K.

## Evaluation E006 — Independent blinded audit

**Total candidates:** 80  
**Label disagreements:** 0  
**Relevant:** 19  
**Irrelevant:** 61

All independent labels matched the original LLM-assisted labels.

Limitation: The original rank-1 labels were seeded before the independent review. Agreement validates the labels against the review process, but the evaluation is not completely independent of the initial relevance selection.

## Evaluation E007 — Top-3 versus Top-5 answer-quality experiment

**Status:** IN PROGRESS

Compare:
- Retrieval context quantity.
- Relevant evidence retained.
- Irrelevant context introduced.
- Answer correctness.
- Answer completeness.
- Citation support.

Control variables:
- Same 16 questions.
- Same corpus.
- Same embedding model.
- Same generation model.
- Same prompt.
- Same evaluation rubric.

Preserve raw outputs for both configurations.

Do not change production Top-K before results are reviewed.

## Future experiment record template

For every experiment, record:

1. Experiment ID and date.
2. Research question.
3. Hypothesis.
4. Dataset and corpus version.
5. Model and version.
6. Prompt and parameters.
7. Experimental procedure.
8. Results.
9. Failure analysis.
10. Limitations.
11. Conclusion.
12. Next experiment.