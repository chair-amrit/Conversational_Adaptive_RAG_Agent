# Conversational Adaptive RAG Agent — Project Handoff

**Last context update:** 6 November 2026  
**Repository:** https://github.com/chair-amrit/Conversational_Adaptive_RAG_Agent  
**Last confirmed branch:** `backup/before-multiformat-dedup`  
**Last confirmed commit:** `b05e88a`

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

## Current evaluation status

Step 9 — Retrieval Quality and Evaluation.

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

Latest judged retrieval results:
- 16 questions.
- 80 retrieved candidates.
- 19 relevant candidates.
- 61 irrelevant candidates.
- Precision@1: 1.00.
- Precision@2: 0.5625.
- Precision@3: 0.3958.
- Precision@4: 0.2969.
- Precision@5: 0.2375.

All 80 independent relevance labels matched the original labels. The original rank-1 labels were seeded, so their agreement is not fully independent evidence of ranking quality.

## Current task: Step 9.6

Controlled Top-3 versus Top-5 answer-quality experiment.

Compare:
- Retrieved context quantity.
- Relevant and irrelevant context.
- Answer correctness.
- Answer completeness.
- Citation support.

Keep the same 16 questions, corpus, embedding model, generation model, prompts, and evaluation rubric.

Do not change production `top_k` until the experiment is complete.

A separate ChatGPT Work session has been created for repository inspection and implementation. Continue that task there.

## Git status

Last confirmed commits:

- `b3d401b` — repeated chunk retrieval diagnostics.
- `4b4180a` — judged retrieval evaluation baseline.
- `fa02a1e` — source concentration report.
- `07ec81d` — judged retrieval cutoff evaluation.
- `b05e88a` — blinded relevance audit workflow.

These were pushed to `backup/before-multiformat-dedup`.

Verify the latest Git state before making further changes.

## Immediate next action

Complete the controlled Top-3 versus Top-5 experiment, inspect its results, document conclusions, and decide whether any retrieval configuration should be changed.

## Continuity rule

At the end of each substantial session, update this file and the relevant roadmap, decision, and evaluation logs.