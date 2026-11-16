import unittest

from nis2eval import paths
from nis2eval.decree_index import DecreeIndex, build_index
from nis2eval.standard import check_evidence, load_standard, validate

IX = DecreeIndex.load()


class Index(unittest.TestCase):
    def test_bodies(self):
        d = build_index()
        self.assertEqual(sorted(map(int, d["sections"]["decreto"]["articles"])), list(range(1, 12)))
        self.assertEqual(sorted(map(int, d["sections"]["regime"]["articles"])), list(range(1, 88)))
        self.assertEqual(sorted(d["sections"]["anexo_iii"]["articles"]), ["1", "2"])

    def test_text_is_repaired(self):
        txt = paths.DECREE_TXT.read_text(encoding="utf-8")
        self.assertIn("incidente significativo", txt)
        self.assertNotIn("ncdente", txt)
        self.assertFalse(any(0xE000 <= ord(c) <= 0xF8FF for c in txt))
        self.assertEqual(len(txt.split("\f")), 65)

    def test_known_provisions(self):
        self.assertIn("24 horas", IX.text_of("regime", 42, 1))
        self.assertIn("duas horas", IX.text_of("regime", 41, 2))
        self.assertIn("30 dias úteis", IX.text_of("regime", 44, 1))
        self.assertIn("7 000 000", IX.text_of("regime", 61, 2, "b", "i"))
        self.assertIn("120 dias", IX.text_of("decreto", 11))
        self.assertEqual(IX.lookup("regime", 42, 1)[0]["page"], 40)
        self.assertEqual(IX.lookup("decreto", 10, 2)[0]["page"], 7)

    def test_alinea_i_is_not_a_subpoint(self):
        node, level = IX.lookup("regime", 27, 1, "i")
        self.assertEqual(level, "point")
        self.assertIn("autenticação multifator", node["text"])


class Standard(unittest.TestCase):
    def test_every_citation_resolves(self):
        self.assertEqual(validate(load_standard(), IX), [])

    def test_shape(self):
        std = load_standard()
        self.assertEqual(len(std["questions"]), 22)
        self.assertEqual(sum(len(q["items"]) for q in std["questions"]), 71)
        self.assertEqual([q["id"] for q in std["questions"] if q["decree_silent"]], ["L2-10", "L2-11", "L2-12"])

    def test_evidence_excerpts_are_on_their_pages(self):
        import copy
        std = load_standard()
        cits = [c for q in std["questions"] for it in q["items"] for c in it["citations"]]
        self.assertEqual(len(cits), 79)
        self.assertTrue(all(c.get("evidence") for c in cits))
        self.assertEqual(check_evidence(std), [])
        bad = copy.deepcopy(std)
        bad["questions"][0]["items"][0]["citations"][0]["page"] += 3   # right excerpt, wrong page
        self.assertEqual(len(check_evidence(bad)), 1)

    def test_questions_come_from_the_authors_file(self):
        import json
        src = json.loads((paths.DATA / "standard" / "source" / "standard-2026-11-15.json").read_text(encoding="utf-8"))
        theirs = {q["id"]: q["question_pt"] for q in src["questions"]}
        self.assertEqual({q["id"]: q["question_pt"] for q in load_standard()["questions"]}, theirs)

    def test_iso27001_absent_from_decree(self):
        self.assertNotIn("27001", paths.DECREE_TXT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
