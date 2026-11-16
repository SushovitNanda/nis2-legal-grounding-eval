"""Scorer tests (T2): one perfect answer must score the maximum, one answer with planted
errors must be caught. The deterministic part is tested for real; the judge is replaced
by a scripted stand-in here - run `python -m nis2eval score` on a real pilot to test the LLM judge."""
import json
import unittest

from nis2eval.blind import cohen_kappa
from nis2eval.citations import citation_summary
from nis2eval.decree_index import DecreeIndex
from nis2eval.judge import build_judge_prompt, normalise, parse_judge_json
from nis2eval.scorer import metrics_from
from nis2eval.standard import load_standard

IX = DecreeIndex.load()
STD = load_standard()
Q = {q["id"]: q for q in STD["questions"]}

PERFECT = ("Nos termos do art. 44.º, n.º 1, o relatório final é enviado no prazo de 30 dias úteis a contar da "
           "notificação do fim do impacto significativo. Se o incidente ainda estiver em curso, a entidade apresenta, "
           "a pedido da autoridade, um relatório intercalar semanal até ao relatório final (art. 44.º, n.º 3).")
PLANTED = ("O relatório final deve ser apresentado no prazo de um mês após a notificação do incidente, nos termos do "
           "artigo 23.º, n.º 4, alínea d), da Diretiva (UE) 2022/2555 e do artigo 144.º, n.º 2, do regime. "
           "A entidade é, com toda a certeza, uma entidade essencial.")


class Deterministic(unittest.TestCase):
    def test_perfect_answer_has_only_valid_citations(self):
        s = citation_summary(PERFECT, IX)
        self.assertEqual((s["n_checked"], s["n_invalid"], s["n_directive"]), (2, 0, 0))

    def test_planted_errors_are_caught(self):
        s = citation_summary(PLANTED, IX)
        self.assertEqual(s["n_invalid"], 1)      # art. 144.º does not exist
        self.assertEqual(s["n_directive"], 1)    # directive cited as the legal basis
        self.assertEqual(s["invalid"][0]["article"], 144)


class Aggregation(unittest.TestCase):
    def test_perfect_scores_max(self):
        q = Q["L1-02"]
        j = normalise({"items": [{"id": "a", "coverage": "covered", "uncertainty": "stated_as_certain"},
                                 {"id": "b", "coverage": "covered", "uncertainty": "stated_as_certain"}],
                       "fabricated_claims": [], "jurisdiction_confusion": {"present": False}}, q)
        m = metrics_from(j, citation_summary(PERFECT, IX), q)
        self.assertEqual((m["coverage"], m["fab_claims"], m["juris_confusion"], m["cit_invalid_rate"]), (1.0, 0, 0, 0.0))

    def test_planted_scores_low(self):
        q = Q["L1-02"]
        j = normalise({"items": [{"id": "a", "coverage": "not_covered"}],  # item b missing on purpose
                       "fabricated_claims": [{"claim": "one month", "why": "decree says 30 working days"},
                                             {"claim": "art. 144.º", "why": "does not exist"}],
                       "jurisdiction_confusion": {"present": True, "examples": ["um mês"]}}, q)
        m = metrics_from(j, citation_summary(PLANTED, IX), q)
        self.assertEqual((m["coverage"], m["fab_claims"], m["fab_any"], m["juris_confusion"]), (0.0, 2, 1, 1))
        self.assertEqual(m["cit_invalid_rate"], 1.0)

    def test_uncertainty_both_ways(self):
        q = Q["L1-07"]  # a, b verified; c, d inferred
        j = normalise({"items": [{"id": "a", "coverage": "covered", "uncertainty": "hedged_without_reason"},
                                 {"id": "b", "coverage": "covered", "uncertainty": "stated_as_certain"},
                                 {"id": "c", "coverage": "covered", "uncertainty": "stated_as_certain"},
                                 {"id": "d", "coverage": "covered", "uncertainty": "flagged"}]}, q)
        m = metrics_from(j, citation_summary("", IX), q)
        self.assertEqual((m["overconf_rate"], m["flag_rate"], m["hedge_rate"]), (0.5, 0.5, 0.5))

    def test_outside_reference_policy(self):
        q = Q["L2-12"]
        j = normalise({"items": [], "outside_reference_claims": [{"claim": "at least once a year", "instrument": "Reg. 756/2026"}],
                       "says_decree_does_not_answer": True}, q)
        cs = citation_summary("", IX)
        self.assertEqual(metrics_from(j, cs, q)["fab_claims"], 0)
        self.assertEqual(metrics_from(j, cs, q, "fabricated")["fab_claims"], 1)
        self.assertEqual(metrics_from(j, cs, q)["admits_gap"], 1)


class JudgePlumbing(unittest.TestCase):
    def test_prompt_contains_what_the_judge_needs(self):
        q = Q["L1-05"]
        p = build_judge_prompt(q, PERFECT, citation_summary(PERFECT, IX), IX)
        for needle in ["status: to confirm", "24 meses", "do decreto", "Jurisdiction confusion", "<answer>"]:
            self.assertIn(needle, p)
        self.assertNotIn("mock", p.lower())

    def test_json_parsing_is_tolerant(self):
        body = {"items": [], "fabricated_claims": []}
        self.assertEqual(parse_judge_json("```json\n" + json.dumps(body) + "\n```"), body)
        self.assertEqual(parse_judge_json("Here is my grading:\n" + json.dumps(body) + "\nDone."), body)

    def test_kappa(self):
        a = ["covered"] * 5 + ["not_covered"] * 5
        self.assertAlmostEqual(cohen_kappa(a, a, ["covered", "partial", "not_covered"])[0], 1.0)
        b = ["covered", "not_covered"] * 5
        self.assertLess(abs(cohen_kappa(a, b, ["covered", "partial", "not_covered"])[0]), 0.25)


if __name__ == "__main__":
    unittest.main()
