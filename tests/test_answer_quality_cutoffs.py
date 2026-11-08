import tempfile
import unittest
from pathlib import Path

from evaluation.evaluate_answer_quality_cutoffs import (
    build_review_rows,
    format_context,
    load_audit_labels,
    load_dataset,
    prompt_fingerprint,
    summarize_context_metrics,
    write_outputs,
)
from llm_utils import generate_chain


class AnswerQualityCutoffTests(unittest.TestCase):
    def test_dataset_is_the_fixed_sixteen_question_benchmark(self):
        dataset = load_dataset()
        self.assertEqual(len(dataset["test_cases"]), 16)
        self.assertEqual(dataset["test_cases"][0]["id"], "Q01")
        self.assertEqual(dataset["test_cases"][-1]["id"], "Q16")

    def test_production_prompt_fingerprint_is_deterministic(self):
        prompt = generate_chain().steps[0]
        first = prompt_fingerprint(prompt)
        second = prompt_fingerprint(prompt)
        self.assertEqual(first, second)
        self.assertRegex(first, r"^[0-9a-f]{64}$")

    def test_completed_blind_labels_join_to_chunk_ids(self):
        labels = load_audit_labels()
        self.assertEqual(len(labels), 80)
        self.assertIn(("Q01", "1b9cd0275418d222443d1f0de9ae1ac9b3fa7f22aceed6751a18aa3deb8bd6cd"), labels)
        self.assertIn(labels[("Q01", "1b9cd0275418d222443d1f0de9ae1ac9b3fa7f22aceed6751a18aa3deb8bd6cd")]["relevance"], {0, 1})

    def test_context_format_matches_page_citation_convention(self):
        context = format_context([
            {"metadata": {"file_name": "manual.pdf", "page": 0}, "content": "PDF text"},
            {"metadata": {"file_name": "deck.pptx", "slide": 2}, "content": "Slide text"},
        ])
        self.assertIn("Source: manual.pdf\nPage 1\nContent:\nPDF text", context)
        self.assertIn("Source: deck.pptx\nPage unknown\nContent:\nSlide text", context)
        self.assertIn("\n\n---\n\n", context)

    def test_context_metrics_keep_unjudged_chunks_distinct(self):
        def condition(labels):
            return {"retrieved_chunks": [
                {"relevance_label": label, "metadata": {"file_name": f"s{index}.pdf"}}
                for index, label in enumerate(labels)
            ], "context": "x" * len(labels)}

        results = [{"conditions": {
            "top3": condition([1, 0, None]),
            "top5": condition([1, 0, None, 1, 0]),
        }}]
        metrics = summarize_context_metrics(results)
        self.assertEqual(metrics["top3"]["reviewer_labeled_relevant_chunks"], 1)
        self.assertEqual(metrics["top3"]["reviewer_labeled_irrelevant_chunks"], 1)
        self.assertEqual(metrics["top3"]["unjudged_chunks"], 1)
        self.assertEqual(metrics["top3"]["share_of_reviewer_labeled_relevant_top5_chunks_retained"], 0.5)

    def test_review_csv_blinds_cutoff_and_writes_private_key(self):
        results = [{
            "question_id": "Q01",
            "question": "Question?",
            "conditions": {
                "top3": {"answer": "A"},
                "top5": {"answer": "B"},
            },
        }]
        review_rows, key_rows = build_review_rows(results)
        self.assertEqual(len(review_rows), 2)
        self.assertNotIn("cutoff", review_rows[0])
        self.assertEqual({row["cutoff"] for row in key_rows}, {3, 5})
        with tempfile.TemporaryDirectory() as directory:
            write_outputs(Path(directory), {"results": results})
            self.assertTrue((Path(directory) / "results.json").is_file())
            self.assertTrue((Path(directory) / "human_review.csv").is_file())
            self.assertTrue((Path(directory) / "answer_key.csv").is_file())


if __name__ == "__main__":
    unittest.main()
