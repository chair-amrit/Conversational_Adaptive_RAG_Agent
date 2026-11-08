# Conversational Adaptive RAG Agent — Project Handoff

**Last context update:** 7 November 2026  
**Repository:** https://github.com/chair-amrit/Conversational_Adaptive_RAG_Agent  
**Active branch:** `backup/before-multiformat-dedup`  
**Latest confirmed commit:** `e4ef491` — `fix: serialize prompt for experiment fingerprinting`

## Project objective

Build a modular, production-oriented conversational RAG framework with reliable ingestion, persistent retrieval, adaptive orchestration, grounded answers, evaluation, and eventual deployment.

## Current implementation

- Multi-format document ingestion.
- Multi-document ingestion.
- ChromaDB persistent vector storage.
- Gemini embeddings.
- Content hashing and deterministic chunk IDs.
- Safe document updates and deletion.
- LangGraph-based adaptive RAG workflow.
- Retrieval grading and permission-gated web fallback.
- Conversational checkpointing.
- Source citation support.
- Retrieval evaluation scripts and datasets.
- Controlled Top-3 versus Top-5 answer-quality experiment implementation.

## Current evaluation status

**Step 9 — Retrieval Quality and Evaluation**

Completed:
- Fixed 16-question evaluation dataset.
- Initial retrieval baseline.
- Precision, Recall and MRR evaluation.
- Retrieval failure analysis.
- LLM-assisted relevance judgements.
- Independent blinded relevance audit.
- Repeated-chunk diagnostics.
- Source concentration analysis.
- Top-K cutoff comparison.
- Experiment implementation and documentation.
- Six offline experiment tests passed after the prompt fingerprint compatibility fix.

### Latest retrieval baseline

- 16 questions.
- 80 retrieved candidates.
- 19 relevant candidates.
- 61 irrelevant candidates.
- Precision@1: 1.0000.
- Precision@2: 0.5625.
- Precision@3: 0.3958.
- Precision@4: 0.2969.
- Precision@5: 0.2375.

The independent blinded audit produced zero label disagreements. Rank-1 labels were seeded before independent review, so agreement is not completely independent evidence of ranking quality.

## Current task: Step 9.6

**Controlled Top-3 versus Top-5 answer-quality experiment.**

The experiment implementation is committed and pushed. Initial generation execution was partially successful.

### Partial execution results

- Questions completed: 8/16.
- Top-3 answers generated: 8.
- Top-5 answers generated: 8.
- Total generated answers: 16/32.
- Remaining questions: Q09–Q16.
- API error: HTTP 429 RESOURCE_EXHAUSTED.
- Cause: Gemini free-tier generation request-per-minute quota.
- Human answer evaluation: Not started.

Partial output location:

`D:\rag_experiments\answer_quality_runs\step-9-6-run-01`

Preserve the partial output. Do not overwrite or regenerate completed question pairs.

### Experiment controls

- Same 16 questions.
- Same Chroma corpus.
- Same Gemini embedding model.
- Same generation model.
- Same production prompt.
- Same source formatting.
- Production retriever remains unchanged at k=10.
- Experimental retrieval uses Top-5, with Top-3 supplied as the ranked prefix.
- Both conditions use empty conversation history.

### Immediate next action

1. Verify that `results.json` contains Q01–Q08 and that the corresponding human-review and answer-key files exist.
2. Implement safe experiment resumption from the first incomplete question.
3. Add bounded HTTP 429 retry handling and controlled request pacing.
4. Add offline tests for resume behaviour and retry logic.
5. Preserve completed results and avoid overwriting existing artifacts.
6. Continue generation for Q09–Q16.
7. Validate all 32 answers before starting blinded human evaluation.

Do not change production retrieval or generation configuration.

## Git status

Last confirmed branch:

`backup/before-multiformat-dedup`

Latest confirmed commit:

`e4ef491` — `fix: serialize prompt for experiment fingerprinting`

Recent commits:

- `f40a578` — paired Top-3 versus Top-5 experiment.
- `bc7f1bc` — experiment validation tests.
- `367b0fc` — experiment methodology documentation.
- `283123d` — Step 9.6 project status.
- `e4ef491` — prompt fingerprint compatibility fix.

All five commits were pushed to the existing working branch.

Verify the latest Git state before further changes.

## Important decisions

- Preserve production Top-K configuration during controlled experimentation.
- Do not treat retrieval precision as a substitute for answer quality.
- Do not treat LLM-as-judge as unquestionable ground truth.
- Preserve raw experiment outputs.
- Keep human-review answers blinded from cutoff information.
- Do not classify unjudged chunks as irrelevant.
- Preserve completed generations when API failures occur.
- Use bounded retries for temporary API quota errors rather than changing production models.

## Unresolved issues

- Complete the remaining eight question pairs.
- Validate the partial run artifacts.
- Implement and test safe resumption.
- Complete human evaluation of correctness, completeness and citation support.
- Analyse paired results and determine whether any retrieval configuration change is justified.

## Roadmap position

**Step 9 — Retrieval Quality and Evaluation.**

Current active task: Step 9.6 — Controlled Top-3 versus Top-5 answer-quality experiment.

The experiment is partially executed, not completed.

## Continuity rule

At the end of each substantial session, update this file and the relevant roadmap, decision, and evaluation logs.