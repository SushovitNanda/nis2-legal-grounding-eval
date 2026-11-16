import unittest

from nis2eval.citations import check_citation, citation_summary, parse_citations
from nis2eval.decree_index import DecreeIndex

IX = DecreeIndex.load()


def P(t):
    return [(c.source, c.articles, c.paragraphs, c.points, c.subpoint) for c in parse_citations(t)]


class ParserFormats(unittest.TestCase):
    def test_portuguese_forms(self):
        self.assertEqual(P("art. 42.º, n.º 1"), [("dl", [42], [1], [], None)])
        self.assertEqual(P("art. 32.º, n.os 3 e 4"), [("dl", [32], [3, 4], [], None)])
        self.assertEqual(P("art. 41.º, n.º 1, als. a) a c)"), [("dl", [41], [1], ["a", "b", "c"], None)])
        self.assertEqual(P("art. 61.º, n.º 2, al. b) i)"), [("dl", [61], [2], ["b"], "i")])
        self.assertEqual(P("artigo 42º nº 1 alínea a)"), [("dl", [42], [1], ["a"], None)])
        self.assertEqual(P("Artigo 30.º, n.º 2 e n.º 4"), [("dl", [30], [2, 4], [], None)])

    def test_inverted_prose_order(self):
        self.assertEqual(P("a alínea b) do n.º 1 do artigo 6.º"), [("dl", [6], [1], ["b"], None)])
        self.assertEqual(P("os n.os 1 e 2 do artigo 27.º"), [("dl", [27], [1, 2], [], None)])
        self.assertEqual(P("alíneas b), c) e f) do n.º 1 do artigo 61.º"), [("dl", [61], [1], ["b", "c", "f"], None)])

    def test_ranges_and_lists(self):
        self.assertEqual(P("arts. 40.º a 44.º")[0][1], [40, 41, 42, 43, 44])
        self.assertEqual(P("artigos 8.º, 14.º, 26.º, 31.º, 32.º e 83.º")[0][1], [8, 14, 26, 31, 32, 83])
        self.assertEqual(P("Articles 41 to 44")[0][1], [41, 42, 43, 44])

    def test_numbers_that_are_not_articles(self):
        self.assertEqual(P("artigo 42.º e 24 horas depois")[0][1], [42])
        self.assertEqual(P("no art. 31.º, n.º 4 (20 dias úteis)"), [("dl", [31], [4], [], None)])

    def test_english_forms(self):
        self.assertEqual(P("Article 42(1) and Article 6(1)(e)"), [("dl", [42], [1], [], None), ("dl", [6], [1], ["e"], None)])

    def test_source_attribution(self):
        self.assertEqual(P("art. 10.º, n.º 2, do decreto")[0][0], "decreto")
        self.assertEqual(P("arts. 40.º a 44.º do regime")[0][0], "regime")
        self.assertEqual(P("artigo 10.º do Decreto-Lei n.º 125/2025")[0][0], "dl")
        self.assertEqual(P("o artigo 23.º da Diretiva (UE) 2022/2555")[0][0], "diretiva")
        self.assertEqual(P("Nos termos da Diretiva NIS 2 (artigo 23.º, n.º 4)")[0][0], "diretiva")
        self.assertEqual(P("Article 23(4)(a) of Directive (EU) 2022/2555")[0][0], "diretiva")
        self.assertEqual(P("Art. 21 of the NIS2 Directive")[0][0], "diretiva")
        self.assertEqual(P("art. 9.º, n.º 2, do Regulamento n.º 756/2026")[0][0], "other")
        self.assertEqual(P("artigo 20.º da Lei n.º 46/2018")[0][0], "other")

    def test_answer_built_on_another_statute(self):
        """Dry run, 14 Nov: a model invented 'Decreto-Lei n.º 157/2024' and cited its articles bare."""
        invented = "O diploma é o Decreto-Lei n.º 157/2024, de 14 de novembro.\nBase legal: Artigo 24.º, n.º 2, alíneas a), b) e c)."
        self.assertEqual([c[0] for c in P(invented)], ["other"])
        self.assertEqual(citation_summary(invented, IX)["n_checked"], 0)
        # once the answer names DL 125/2025, bare articles are checked as before
        named = "O Decreto-Lei n.º 125/2025 revogou a Lei n.º 46/2018. Ver o artigo 41.º, n.º 2."
        self.assertEqual([c[0] for c in P(named)], ["dl"])
        # a statute mentioned only after the citation does not capture it
        self.assertEqual(P("Nos termos do artigo 41.º, n.º 2. A Lei n.º 46/2018 foi revogada.")[0][0], "dl")


class CheckAgainstDecree(unittest.TestCase):
    def verdicts(self, t):
        return [r["verdict"] for c in parse_citations(t) for r in check_citation(c, IX)]

    def test_existing(self):
        for t in ["art. 42.º, n.º 1", "art. 61.º, n.º 1, al. j)", "art. 61.º, n.º 2, al. b) i)", "art. 27.º, n.º 1, al. i)",
                  "art. 10.º, n.º 2, do decreto", "art. 64.º", "art. 28.º, al. e)", "art. 2.º, al. mm)"]:
            self.assertEqual(self.verdicts(t), ["valid"], t)

    def test_planted_errors(self):
        self.assertEqual(self.verdicts("artigo 142.º, n.º 3"), ["no_article"])
        self.assertEqual(self.verdicts("art. 42.º, n.º 9"), ["no_paragraph"])
        self.assertEqual(self.verdicts("art. 61.º, n.º 1, al. z)"), ["no_point"])
        self.assertEqual(self.verdicts("art. 12.º do decreto"), ["no_article"])  # the decree itself has 11 articles

    def test_decree_vs_regime_trap(self):
        """art. 10.º exists in both bodies; they are different rules."""
        r_dec = check_citation(parse_citations("art. 10.º, n.º 2, do decreto")[0], IX)[0]
        r_amb = check_citation(parse_citations("art. 10.º, n.º 2")[0], IX)[0]
        self.assertEqual((r_dec["resolved"], r_dec["page"], r_dec["ambiguous"]), ("decreto", 7, False))
        self.assertTrue(r_amb["ambiguous"])
        self.assertIn("24 meses", IX.text_of("decreto", 10, 2))
        self.assertNotIn("24 meses", IX.text_of("regime", 10) or "")

    def test_other_instruments_not_checked(self):
        self.assertEqual(self.verdicts("artigo 23.º da Diretiva (UE) 2022/2555"), ["not_checked"])

    def test_directive_citations_checked_against_the_directive(self):
        from nis2eval.directive_index import crosscheck, load_directive_index
        dx = load_directive_index()
        if dx is None:
            self.skipTest("directive text not in the repository")
        self.assertEqual(dx.n_articles("diretiva"), 46)
        s = citation_summary("O artigo 23.º, n.º 4, alínea a), da Diretiva (UE) 2022/2555 e o artigo 99.º da Diretiva NIS 2.", IX)
        self.assertEqual((s["n_directive"], s["n_directive_invalid"], s["n_checked"]), (2, 1, 0))
        from nis2eval import paths
        if paths.DIRECTIVE_TXT_EN.exists():  # Portuguese C2 text vs the official English PDF
            self.assertEqual(crosscheck(log=lambda *_: None), [])

    def test_summary_counts(self):
        s = citation_summary("Nos termos do art. 42.º, n.º 1, e do artigo 142.º; ver o artigo 23.º da Diretiva NIS 2 "
                             "e a Lei n.º 46/2018.", IX)
        self.assertEqual((s["n_citations"], s["n_checked"], s["n_invalid"], s["n_directive"]), (3, 2, 1, 1))
        self.assertTrue(s["mentions_repealed"])


if __name__ == "__main__":
    unittest.main()
