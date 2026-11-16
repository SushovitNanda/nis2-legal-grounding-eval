"""The standard can still change after a run has started. Only what changed is redone."""
import copy
import tempfile
import unittest
from pathlib import Path

from nis2eval.decree_index import DecreeIndex
from nis2eval.llm import MockClient
from nis2eval.runner import latest_ok, read_jsonl, run
from nis2eval.scorer import score_run
from nis2eval.standard import load_standard

IX = DecreeIndex.load()
QUIET = lambda *a, **k: None


class Resume(unittest.TestCase):
    def setUp(self):
        self.std = load_standard()
        self.std["questions"] = self.std["questions"][:3]
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, std):
        return run(MockClient(std), std["questions"], ["mock-large"], ["C0", "C1"], 2, self.dir, mock=True, log=QUIET)

    def _score(self, std):
        score_run(MockClient(std), "mock-judge", std, IX, self.dir, log=QUIET)
        return [r for r in read_jsonl(self.dir / "judgments.jsonl") if r["status"] == "ok"]

    def test_rerun_skips_what_is_done(self):
        self.assertEqual(self._run(self.std)["ok"], 12)
        again = self._run(self.std)
        self.assertEqual((again["ok"], again["skipped"]), (0, 12))

    def test_reworded_question_is_asked_again(self):
        self._run(self.std)
        new = copy.deepcopy(self.std)
        new["questions"][1]["question_pt"] += " Fundamente."
        again = self._run(new)
        self.assertEqual((again["ok"], again["skipped"]), (4, 8))
        answers = latest_ok(self.dir / "answers.jsonl")
        self.assertEqual(len(answers), 12)
        self.assertTrue(all(a["question"] == q["question_pt"] for a in answers
                            for q in new["questions"] if q["id"] == a["qid"]))
        self.assertEqual(self._run(new)["ok"], 0)

    def test_revised_checklist_is_judged_again(self):
        self._run(self.std)
        self.assertEqual(len(self._score(self.std)), 12)
        self.assertEqual(len(self._score(self.std)), 12)            # nothing changed: nothing judged twice
        new = copy.deepcopy(self.std)
        new["questions"][0]["items"][0]["text_en"] += " (revised)"
        self.assertEqual(len(self._score(new)), 16)                 # only that question's 4 answers
        new["questions"][2]["question_pt"] += " Fundamente."
        self._run(new)
        self.assertEqual(len(self._score(new)), 20)                 # only the 4 new answers
        import csv
        with (self.dir / "scores.csv").open(encoding="utf-8") as f:
            self.assertEqual(len(list(csv.DictReader(f))), 12)


if __name__ == "__main__":
    unittest.main()
