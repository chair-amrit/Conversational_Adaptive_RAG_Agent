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

### Research question

Does retaining three retrieved chunks instead of five change generated answer correctness, completeness and citation support for the fixed 16-question evaluation dataset?

### Experimental controls

- Same 16 questions.
- Same Chroma corpus.
- Same Gemini embedding model.
- Same generation model.
- Same production prompt.
- Same source formatting.
- Same evaluation rubric.
- Production retriever configuration remains unchanged.

### Implementation status

The experiment runner, offline tests and methodology documentation have been committed.

Prompt fingerprint compatibility was fixed using LangChain's `dumpd()` serialization.

Six offline tests passed after the fix.

### Partial execution — 7 November 2026

**Output directory:**

`D:\rag_experiments\answer_quality_runs\step-9-6-run-01`

| Measurement | Result |
|---|---:|
| Evaluation questions | 16 |
| Completed question pairs | 8 |
| Top-3 answers generated | 8 |
| Top-5 answers generated | 8 |
| Total answers generated | 16/32 |
| Remaining question pairs | 8 |
| API error | HTTP 429 RESOURCE_EXHAUSTED |

The API error was caused by the Gemini free-tier generation request-per-minute quota.

The execution stopped after Q08. Q09–Q16 were not generated.

### Interpretation

These are execution and generation counts only.

No answer-quality conclusions can be drawn from the partial run.

Correctness, completeness and citation support have not yet been evaluated.

### Recovery plan

1. Verify the existing `results.json`, `human_review.csv` and `answer_key.csv`.
2. Preserve all completed outputs.
3. Implement safe resumption from the first incomplete question.
4. Add bounded HTTP 429 retry handling and request pacing.
5. Test recovery behaviour without Gemini API calls.
6. Generate the remaining Q09–Q16 answer pairs.
7. Validate all 32 generated answers.
8. Conduct blinded human evaluation.
9. Analyse paired per-question differences.

### Human answer-review rubric

| Score | Correctness | Completeness | Citation support |
|---:|---|---|---|
| 0 | Material factual error, unsupported claim, or fails to answer. | Omits the answer or misses material parts. | Citations absent where needed, incorrect, or unsupported. |
| 1 | Partly correct, with a material error or ambiguity. | Answers some but not all requested parts. | Some claims supported, but at least one material claim is uncited or unclear. |
| 2 | Factually correct and consistent with the source. | Covers all requested parts at an appropriate level of detail. | Each material document-based claim is supported by a correct citation. |

Use human-reviewable evidence and reviewer notes.

Do not use an LLM as the sole judge.

### Limitations

- Only 16 questions are included.
- There is one generation per condition.
- Generation can vary between calls.
- Provider quota and model behaviour can affect execution.
- Retrieval relevance labels are not complete answer ground truth.
- Findings will be descriptive and limited to this evaluation set.

Do not change production Top-K before reviewing the complete paired experiment.

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