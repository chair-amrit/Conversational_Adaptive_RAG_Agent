# Technical Learning Log

## Learning objective

Develop deep AI engineering knowledge by understanding the design, implementation, testing, and deployment of the RAG framework.

The objective is not simply to make the application work. It is to understand why it works, where it fails, and how to improve it.

## Concepts already explored

### Vector databases
- FAISS versus ChromaDB.
- Persistent vector storage.
- Collections and metadata.
- Embedding-based retrieval.

### Document ingestion
- Multi-format loaders.
- Text splitting.
- Chunk size and overlap.
- Content hashing.
- Deterministic chunk IDs.
- Duplicate detection.
- Safe update and deletion.

### Conversational orchestration
- LangGraph nodes and edges.
- Conditional routing.
- Retrieval grading.
- Query rewriting.
- Conversational checkpointing.
- Permission-gated web fallback.

### Retrieval evaluation
- Precision@K.
- Recall@K.
- Mean Reciprocal Rank.
- HitRate.
- Relevance judgements.
- Retrieval noise.
- Chunk repetition.
- Source concentration.
- Cutoff selection.
- Passage relevance versus answer completeness.

## Current learning priority

Understand how retrieval context affects final answer quality.

Study:
- Context selection.
- Retrieval precision versus answer quality.
- Context noise.
- Answer faithfulness.
- Completeness.
- Citation grounding.
- LLM-as-judge limitations.
- Evaluation reproducibility.

## Learning methodology

For each major technical concept:

1. Understand the theory.
2. Understand the implementation.
3. Compare alternatives.
4. Identify failure modes.
5. Implement or inspect a working example.
6. Evaluate the result.
7. Explain the decision in your own words.

## Knowledge gaps

Update this section as new gaps are discovered.

Do not mark a topic as mastered merely because an implementation works.