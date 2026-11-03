@'
# Retrieval Evaluation Baseline

## Dataset
- 16 evaluation questions
- 4 source documents
- Chroma vector database
- Gemini Embedding 001
- Initial retrieval configuration: k=10

## Baseline Results

| Metric | Top 5 | Top 10 |
|---|---:|---:|
| Precision@K | 0.2125 | 0.1063 |
| Recall@K | 1.0000 | 1.0000 |
| MRR@K | 1.0000 | 1.0000 |
| Expected source share | 0.7000 | 0.3875 |

## Observations
- All 16 queries retrieved their labelled relevant chunks.
- All 16 queries ranked at least one relevant chunk first.
- Top 5 produced better precision under the current relevance labels.
- Cross-document retrieval noise was observed.

## Limitations
The benchmark uses manually assigned relevant chunk IDs.
Complete human relevance judgements are still pending.
These results represent an initial baseline, not a comprehensive evaluation.
'@ | Set-Content .\docs\retrieval-baseline.md