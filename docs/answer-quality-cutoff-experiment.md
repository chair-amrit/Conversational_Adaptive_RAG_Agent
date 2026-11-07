# Top-3 vs Top-5 answer-quality experiment

## Purpose and boundary

This paired experiment asks whether keeping three retrieved chunks instead of
five changes generated answer quality for the existing 16 questions. It does
not change the production retriever, which remains configured with `k=10` in
`rag_utils.py`.

The fixed input is `evaluation/retrieval_eval_dataset.json`. Its `Q01`–`Q16`
records provide question text, a target source, and relevant chunk IDs; they do
not contain complete reference answers. Do not infer or add gold answers from
those fields. Answer correctness, completeness, and citation support are left
for human review against the source documents.

## Controlled procedure

For each question, the runner embeds the question once with
`models/gemini-embedding-001` and queries the existing `my_rag_multiformat`
Chroma collection for five results. It then sends ranks 1–3 and ranks 1–5 as
the two contexts. Top-3 is therefore exactly the prefix of that question's
Top-5 result. The embedding model, Chroma collection snapshot, question,
generation model (`gemini-3.5-flash-lite`), production answer prompt, source
formatting, and empty conversation history are identical across conditions.
Each answer is generated once; the order of Top-3 and Top-5 calls is shuffled
with a fixed seed and recorded per question. Provider sampling defaults are
left as configured by the production `generate_chain()`.

The experiment records each chunk's rank, Chroma ID, distance, metadata, full
text, context string, answer, the production prompt hash, dataset hash, and a
hash of all IDs/text/metadata in the Chroma collection at run time. It checks
that all dataset gold chunk IDs exist and belong to the declared source before
calling generation.

The runner joins the completed blinded retrieval audit to returned chunks by
`(question_id, chunk_id)`. It reports labeled relevant, labeled irrelevant,
and unjudged chunks separately. A chunk absent from the reviewed Top-5 pool is
unjudged; it is never assumed irrelevant. The context metrics are descriptive
of retrieved chunks and text length, not generated-answer quality or exact
token cost. The three partial-coverage cases remain relevant under the labels
already recorded in the audit.

## Human answer-review rubric

Review the two answers for a question independently, without looking at the
cutoff. Use the source document named in `expected_source_from_dataset` and
inspect the answer's citations against the retrieved evidence in `results.json`.
Record one integer per dimension:

| Score | Correctness | Completeness | Citation support |
|---:|---|---|---|
| 0 | Material factual error, unsupported claim, or fails to answer. | Omits the answer or misses the material parts of the question. | Citations are absent where needed, point to the wrong source/location, or do not support the associated claims. |
| 1 | Partly correct, with a material error or ambiguity. | Answers some but not all requested parts. | Some claims are supported, but at least one material claim is uncited or its citation is incomplete/unclear. |
| 2 | Factually correct and consistent with the source. | Covers all requested parts at an appropriate level of detail. | Each material document-based claim is supported by a correct citation to retrieved evidence. |

If a question cannot be answered from its retrieved context, an explicit
abstention can be correct (2) but is incomplete (0 or 1) when the source does
contain the requested information. Use reviewer notes to explain borderline
scores. Do not use a language model as the sole judge. The fixed questions and
retrieval labels are not substitutes for answer ground truth.

`human_review.csv` contains 32 shuffled answer rows with opaque response IDs;
it intentionally hides the cutoff. Keep `answer_key.csv` private until scoring
is complete. Join scores by `response_id`, then use the key to restore each
question/cutoff pair. Report the three dimensions separately, per-condition
means, and paired per-question differences. With only 16 questions and one
generation per condition, treat those summaries as descriptive; do not claim a
reliable general effect from a significance test or a small mean difference.

## Run

From the repository root, with the existing virtual environment and Gemini API
credentials available through `.env`:

```powershell
.\venv\Scripts\python.exe .\evaluation\evaluate_answer_quality_cutoffs.py
```

The script creates a new UTC timestamped folder under
`evaluation/answer_quality_runs/`. To choose a folder explicitly, use a fresh
path for every run:

```powershell
.\venv\Scripts\python.exe .\evaluation\evaluate_answer_quality_cutoffs.py `
  --output-dir .\evaluation\answer_quality_runs\manual-run-01
```

Each run writes:

- `results.json`: run provenance, retrieved evidence and both answers; updated
  after each question pair so completed work remains inspectable if a later
  model call fails.
- `human_review.csv`: shuffled scoring template with cutoff hidden.
- `answer_key.csv`: private mapping from response ID to question and cutoff.

Do not share the answer key with the reviewer before they complete scoring.
After review, preserve the original files and save a scored copy of
`human_review.csv`; aggregate it only after validating all 32 rows and score
values are present.

## Validation and limitations

Run the offline checks with:

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -p "test_answer_quality_cutoffs.py"
```

The benchmark has 16 questions across four target documents. The reviewed
relevance labels cover only the prior Top-5 pool. Gemini model aliases and
provider defaults can change, and generation may vary between calls. The
artifact records the model name, exact prompt hash, corpus hash, and call order,
but does not freeze provider internals. Context length is reported in
characters, not billed tokens. Source formatting mirrors production: PDF page
metadata is rendered one-indexed, while formats without a page field currently
receive `Page unknown`, even if their metadata contains a slide, sheet, or
record index. Citation review must account for this existing behavior.

The result supports a decision about this fixed evaluation set only. Do not
change production `top_k` based on retrieval precision alone or before
reviewing the paired generated answers.
