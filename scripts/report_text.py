"""Text of the submission report. scripts/build_report.py pours it into the Apart template.

Inline marks: **bold**, *italic*. Every number in the prose comes from results/full/RESULTS_tables.md
or results/full/judge_agreement.md; the tables themselves are read from those files at build time.
"""

# Set this to the public repository's address, then run  python scripts/build_report.py
REPO_URL = ""

TITLE = "Grounded or Guessing? What the Legal Text Does to LLM Compliance Advice on Portugal's NIS 2 Transposition"

AUTHORS = [("Beatriz Lourenço", "University of Lisbon, School of Law"), ("Sushovit Nanda", "Independent Researcher")]   # non-breaking space: a name stays on one line

ABSTRACT = (
    "Retrieval is the main way to ground the legal advice that language models give; we test when it delivers. Our case is Decreto-Lei n.º 125/2025, Portugal's "
    "transposition of the NIS 2 Directive, published in December 2025 and unknown to the four models we test. A legal "
    "professional wrote 22 compliance questions and a 71-item checklist, each item cited to the official text and "
    "marked as verified, inferred or to confirm. Each model answered each question with no document, with the "
    "decree-law, and with the Directive instead (792 answers). Two LLM judges from different families graded every "
    "answer against the checklist and the full legal text, a parser checked every citation, and the judges agree with "
    "a legal professional's blind grades (Cohen's kappa 0.64 to 0.92). The right text transforms the advice: "
    "checklist coverage rises from 27% to 88% and the share of answers with an unsupported claim falls from 95% to 10%. "
    "The related text exposes a failure that citation checks cannot see: with the Directive, coverage stays at 26% "
    "while 94% of answers apply it as if it were Portuguese law, citing provisions that are real. Models flag "
    "uncertainty where the text signals it. Grounded legal advice is only as reliable as the applicability of its "
    "source, and we provide a reusable design, an expert-built standard and an open pipeline to test exactly that."
)

SUPPLEMENTARY_MODEL = "gemma-4-26b-a4b-it"

ROW_LABELS = {
    "Answers with at least one unsupported claim": "Answers with at least one unsupported claim",
    "Answers with jurisdiction confusion": "Answers with jurisdiction confusion",
    "Uncertain items properly flagged": "Uncertain checklist items properly flagged",
    "Says the decree does not settle the point": "Says the decree does not settle the point (3 questions)",
    "Says the text given is not the Portuguese law": "Says the text given is not the Portuguese law",
}

TABLE2_CAPTION_NO_HUMAN = (
    "**Table 2.** Agreement between the two LLM judges on all 792 answers: Cohen's kappa, with raw agreement in "
    "brackets. Both judges received the same prompt, rubric and full text of the decree-law.")


def human_paragraph(human: dict) -> str:
    if not human:
        return ("**Human validation.** The author of the standard is grading a blind sample of 25 answers, stratified "
                "over models and conditions, with the same rubric and without seeing the judges' marks.")
    def k(j, m):
        v = human.get(j, {}).get(m)
        return f"{v[0]:.2f}" if v and v[0] == v[0] else "n/a"
    q, g = "qwen3.8-27b", "gemma-4-31b-it"
    # The counts below are from results/full/blind/human_results.md (scripts/human_results.py).
    return ("**Human validation.** The author of the standard graded a blind sample of 25 answers (8 or 9 per "
            "condition) with the same rubric, without seeing model, condition or the judges' marks. The judges agree "
            f"with her substantially on item coverage (weighted kappa {k(q, 'coverage (linear-weighted)')} and "
            f"{k(g, 'coverage (linear-weighted)')}) and on whether an answer contains an unsupported claim "
            f"({k(q, 'fab_any')} and {k(g, 'fab_any')}), and almost perfectly on jurisdiction confusion "
            f"({k(q, 'jurisdiction')} and {k(g, 'jurisdiction')}; Table 2). On the 15 answers she graded without any "
            "assistance (Appendix A), agreement is as high (coverage 0.67 and 0.63; unsupported claim 0.86 for both; "
            "jurisdiction 0.87 and 1.00). Her grades alone reproduce the main result: coverage 12% / 88% / 40% for "
            "C0 / C1 / C2, an unsupported claim in 8 of 8 / 2 of 9 / 8 of 8 answers, jurisdiction confusion in 7 / 0 / 8. "
            "Her notes add the legal diagnosis: every one of the 16 answers without the decree-law rests on a wrong legal "
            "basis (the Directive in 9, a statute that is not the transposition in 8, the repealed Lei n.º 46/2018 in 4), "
            "and every one of the 9 with it rests on the decree-law (Appendix I).")


SECTIONS = [
    ("1. Introduction", [
        ("p", "Following Directive (EU) 2022/2555 on measures for a high common level of cybersecurity across the Union "
              "(NIS 2 Directive), a company that falls under a transposition cybersecurity law is faced with practical "
              "questions: must it register, with whom and by when; what must it send the authority after an incident; "
              "what does it risk if it does not. More and more often the first answer comes from a language model. Legal "
              "advice is a demanding test of an assistant's epistemics: an answer that gives the wrong deadline, or the "
              "right deadline of the wrong legal instrument, reads as fluently as a correct one. Two properties matter more "
              "than eloquence: whether each claim rests on the law in force, and whether the answer says what is not "
              "settled. Retrieval-augmented generation is the standard way to secure the first, so knowing when grounding "
              "works, and when it only appears to, matters for every deployed assistant that cites its sources."),
        ("p", "European law makes the question sharp. Within the EU, a Directive binds each Member State as to the result "
              "to be achieved and leaves the choice of form and methods to national authorities (Article 288 TFEU), so a "
              "company's duties come from the national transposition rather than the Directive itself; the Court of "
              "Justice has held that a directive can have direct effect only against the State, not against an individual "
              "(Van Duyn v Home Office, Case 41/74; Ratti, Case 148/78). Portugal transposed it through Decreto-Lei "
              "n.º 125/2025 of 4 December 2025, which departs from the Directive on points a company must act on."),
        ("p", "For a significant incident the Directive provides for an early warning within 24 hours, a notification "
              "within 72 hours and a final report within one month; the decree-law provides for an initial notification, "
              "a notification of the end of significant impact and a final report within 30 working days of that "
              "notification (art. 44.º, n.º 1, of the regime), reduced to one notification when the incident is resolved "
              "within two hours. A model that knows the Directive but not the national law therefore has a specific way "
              "to be wrong, which we call *jurisdiction confusion*: answering a question about Portuguese law from the "
              "Directive, from another State's law or from a repealed statute."),
        ("p", "The decree-law was published after the training cutoffs of three of the four models we test, and none "
              "recognises it when asked. This allows a clean test: what a model does without the law, what the text adds, "
              "and what happens when the text supplied is official and related but not the applicable law, as when "
              "retrieval returns the EU directive for a question about national law."),
        ("p", "We ask: does giving a model the law make its compliance advice more complete, better grounded and more "
              "honest about what is uncertain, and what happens when the document is the wrong one? Our main "
              "contributions are:"),
        ("num", [
            "**An expert-built reference standard** for a statute no model has seen: 22 compliance questions and 71 "
            "checklist items, each with article, paragraph, page and a literal excerpt of the official text, and each "
            "marked verified, inferred or to confirm, including three questions the statute does not answer, leaving them "
            "for regulation (CNCS Regulation 756/2026).",
            "**A wrong-document evaluation design** (no text, the right text, a related official text that does not "
            "apply) on four models and 792 answers, scored by two LLM judges validated against a legal professional's "
            "blind grades and by a deterministic citation check against both legal texts.",
            "**Three findings.** The right text turns guessing into grounded advice (coverage 27% to 88%; answers with "
            "an unsupported claim 95% to 10%). A related official text adds nothing to coverage yet makes the advice "
            "look grounded, with 94% of answers applying a text that does not govern the question. Models flag "
            "uncertainty where the text itself signals it.",
            "**An open, reproducible pipeline and dataset**: code, the standard with evidence excerpts, all answers "
            "with both judges' marks and the human grades, and one command that rebuilds every table and this report.",
        ]),
    ]),
    ("2. Related Work", [
        ("p", "**Legal hallucination.** Dahl et al. (2024) asked general-purpose models verifiable questions about United "
              "States case law and found hallucinations in at least 58% of answers. Magesh et al. (2025) showed that "
              "commercial legal research tools built on retrieval still hallucinate in more than 17% of queries. Both "
              "study case law in English. We study statutory compliance advice in a civil-law jurisdiction, in Portuguese, "
              "on a statute the models cannot have seen, and we vary the document given to the model, not the tool."),
        ("p", "**Legal benchmarks.** LegalBench (Guha et al., 2023) collects 162 tasks built with legal professionals, "
              "mostly classification and short answers. Its answer keys do not record how certain the legal position is; "
              "our checklist items carry that status, so we can measure calibration as well as correctness."),
        ("p", "**Context and retrieval.** Retrieval-augmented generation (Lewis et al., 2020) rests on the premise that "
              "supplying a document grounds the answer. Models follow a supplied context over what they learned in "
              "training (Longpre et al., 2021) and can be misled by irrelevant retrieved text (Yoran et al., 2024). Our third condition is a legally meaningful version of this: the document is "
              "relevant, official and on the same subject, but it is not the law that applies."),
        ("p", "**LLM judges.** Model judges can agree with human raters at the level humans agree with each other "
              "(Zheng et al., 2023), but they favour their own outputs (Panickssery et al., 2024). We use two judges from "
              "different families, report every result without the judge's own answers, and validate both against a "
              "legal professional. To our knowledge, no prior evaluation combines a professionally cited answer key with "
              "epistemic status, a wrong-but-related document condition, and a statute published after the models' training."),
    ]),
    ("3. Methods", [
        ("p", "**Reference standard.** A legal professional on the team (B.L.: law degree and postgraduate qualification in "
              "AI and Law, University of Lisbon; seven years of legal practice) wrote 22 open-ended compliance questions about "
              "Decreto-Lei n.º 125/2025, chosen where the decree-law departs from the Directive. Each question has a "
              "checklist of what a correct answer must contain: 71 items, two to five per question. Every item carries a "
              "citation (article, paragraph, point, page of the official PDF, and a literal excerpt) and an epistemic "
              "status: *verified* in the official text (60 items), *inferred*, for example a date calculation or the "
              "reading of an ambiguous provision (4), or *to confirm*, depending on regulation or facts outside the "
              "decree (7). Three questions are ones the decree-law does not answer. All 79 citations were verified by the "
              "author and by two scripts against the official PDF. A pilot on ten questions let the author sharpen the "
              "standard before it was frozen."),
        ("p", "**Conditions.** Each model answered each question under three conditions that differ only in the document "
              "placed before the question. *C0*: no document. *C1*: the full official text of the decree-law (65 pages, "
              "52,000 to 56,000 tokens). *C2*: the official Portuguese text of the Directive instead, articles and annexes "
              "without recitals (42,000 to 44,000 tokens), labelled truthfully as the Directive. The prompt, in Portuguese, asks about Portuguese law in force and asks for a "
              "complete answer with its legal basis. It does not mention uncertainty, so that we measure whether the "
              "model raises it unprompted. Each cell was sampled three times at temperature 0.7: 22 x 4 x 3 x 3 = 792 "
              "answers, none missing."),
        ("p", "**Models.** qwen3.5-397b, qwen3.8-27b (the same family at a fifteenth of the size), gemma-4-31b-it and "
              "deepseek-v4-flash, called through Adaption's hosted inference API on 14 and 15 November 2026 at reasoning "
              "effort \"medium\" with 12,000 output tokens. Published training cutoffs are January, April and May 2025 "
              "for three of them; qwen3.8-27b has none published. Asked without any text what Decreto-Lei n.º 125/2025 "
              "is, all four said they did not know it."),
        ("p", "**Scoring.** *Citation check.* A parser extracts every article reference from an answer, attributes it to "
              "the decree-law, the Directive or another instrument, and looks it up in an index of that text. The "
              "decree-law has two bodies that both begin at article 1 (the decree and the annexed regime); the index "
              "keeps them apart. *LLM judge.* A judge at temperature 0 reads the full decree-law, the checklist with "
              "statuses and grading notes, and the citation check, blind to model and condition. "
              "It marks each checklist item as covered, partial or not covered and, separately, whether the answer "
              "states it as certain, flags what it depends on, or hedges without reason. It lists *unsupported claims*: "
              "any claim with no support in the decree-law or contrary to it, one underlying error counted once (the "
              "rubric's \"fabricated\"; a rule of the Directive stated as Portuguese law is one). It also marks "
              "jurisdiction confusion. Coverage is the mean item score (partial = 0.5)."),
        ("p", "**Judges and validation.** Because LLM judges favour their own outputs (Panickssery et al., 2024), the "
              "design checks the judges three ways. The main judge, qwen3.8-27b, and a second judge from another family, "
              "gemma-4-31b-it, graded every answer with the same prompt. Both are also test models, so every result is "
              "reported without the judge's own answers: the main result covers qwen3.5-397b, gemma-4-31b-it and "
              "deepseek-v4-flash (594 answers). And the author of the standard graded a blind sample of 25 answers, "
              "stratified over models and conditions, with the same rubric."),
        ("p", "**Statistics.** The unit of analysis is the question, because repetitions of one question are not "
              "independent. Repetitions and models are averaged within a question, and 95% intervals come from 5,000 "
              "bootstrap resamples of the 22 questions. Condition effects are paired differences per question."),
    ]),
    ("4. Results", [
        ("p", "Table 1 and Figure 1 give the main result for the three models that are not the main judge."),
        ("table_main", "**Table 1.** Main result. Three models (qwen3.5-397b, gemma-4-31b-it, deepseek-v4-flash), 594 "
                       "answers, judge qwen3.8-27b. Means over 22 questions; 95% bootstrap intervals over questions in brackets."),
        ("fig", "**Figure 1.** Four rows of Table 1 by condition. Bars: mean over questions (models and repetitions "
                "averaged within a question first); lines: 95% bootstrap interval over questions. The rightmost panel "
                "covers only the three questions that the decree-law does not answer."),
        ("p", "**With the decree-law, the models answer from it.** Coverage rises from 27% to 88% (paired difference per "
              "question +61 points, 95% interval +51 to +69), and the share of answers with an unsupported claim falls from "
              "95% to 10% (-85 points, -93 to -73); both intervals lie far from zero. No answer confused the Directive with "
              "national law. Of the 4,954 citations to the decree-law in these answers (all four models), 98.2% point to a "
              "provision that exists."),
        ("p", "**Without the text, the models answer anyway, from the wrong sources.** The same models that say they do "
              "not know the decree-law produce a full compliance answer when asked a compliance question: 95% of those "
              "answers contain an unsupported claim, 3.9 on average. None of the 264 answers without a document names "
              "Decreto-Lei n.º 125/2025; 154 (58%) rest on the regime it repealed (Lei n.º 46/2018 or Decreto-Lei "
              "n.º 65/2021), and 153 (58%) name some other statute dated 2023 to 2026 as the transposition."),
        ("p", "**With the Directive instead, the models apply it as Portuguese law.** Coverage is the same as with no "
              "text at all (26% against 27%; difference 0 points, -6 to +6), because the Directive does not contain the "
              "national rules the questions ask about. But 94% of these answers show jurisdiction confusion, against 58% "
              "with no text, and only 14% say that the text they were given is not the Portuguese law. Their citations are real: of 4,157 "
              "citations to the Directive, 96.8% exist. The error lies in applying the Directive, not in inventing it: "
              "157 of the 168 answers with an unsupported claim under C2 also show jurisdiction confusion."),
        ("p", "**Uncertainty is flagged where the text signals it.** With the decree-law, of 99 marks on the 11 items the "
              "standard marks as inferred or to confirm, 42 flag the doubt, 29 state the point as certain and 28 do not "
              "address it; without it, 93% are not addressed. Where the decree says a matter is left to regulation, the "
              "models say so (9 of 9 on two such items). Where the point needs a date calculation, they state as certain "
              "what the standard marks as inferred (L1-07 d: 8 of 9); for L1-03 c the doubt comes from CNCS Regulation "
              "756/2026, which the models were not given. Every answer given with the decree says when the decree does "
              "not settle a question (27 of 27; 30% with no text, 11% with the Directive)."),
        ("h3", "Robustness"),
        ("p", "**Second judge and per model.** Graded by gemma-4-31b-it, without its own answers, coverage is 17% / 88% / "
              "27% and answers with an unsupported claim 98% / 13% / 97% for C0 / C1 / C2: the same conclusions. The "
              "pattern holds for each model (coverage with the decree-law 82% to 95%, without it 18% to 32%; Appendix D) "
              "and for a fifth, gemma-4-26b-a4b-it (19% / 81% / 24%; Appendix H)."),
        ("table_agreement", "**Table 2.** Agreement of the judges with each other (792 answers) and with the human grader "
                            "(blind sample of 25 answers): Cohen's kappa, with raw agreement in brackets."),
        ("human", None),
    ]),
    ("5. Discussion and Limitations", [
        ("p", "**Grounding works.** With the applicable text in the prompt, four models of different families and sizes "
              "covered most of what a lawyer required and almost stopped making unsupported claims. For a law the models "
              "cannot know, the document does the work."),
        ("p", "**The wrong document looks like success.** Under C2, 97% of the Directive citations verify, so a guardrail "
              "that checks whether cited provisions exist would pass these answers. Yet an answer that applies a directive "
              "article to a Portuguese company as a duty cites the wrong source of law, even when the rule is accurately "
              "stated: one blind-sample answer reasons from the Directive, which has no entity-level cybersecurity "
              "officer, and concludes there is no such obligation; art. 31.º, n.º 1 of the decree-law requires one. Only "
              "one answer in seven noticed the mismatch, although the text was labelled as the Directive."),
        ("p", "**Implications for AI safety and epistemics.** Grounding moves the reliability question from the model to "
              "the retrieval step, and our results show that the usual audit, citation validity, does not catch the "
              "failure that matters: a verifiable citation can make wrong advice more convincing, not less. The check "
              "that matters is applicability: does the instrument cited govern the question asked? This generalises "
              "beyond law to any domain with layered or versioned sources (standards, clinical guidelines, regulations "
              "and their national implementations), and our wrong-but-related condition is a cheap, reusable test for "
              "it. Without the text the models did not abstain: they said they did not know the decree-law, then answered "
              "compliance questions in full. Calibration followed the text: uncertainty was "
              "flagged where the decree says a matter is left to regulation, and less where the standard's doubt comes "
              "from a date calculation or a reading of the provision."),
        ("h3", "Limitations"),
        ("p", "The study covers one statute and 22 questions; the uncertainty metrics rest on 11 items, so their "
              "intervals are wide. Both judges are language models and also test models, which we address by reporting "
              "results without each judge's own answers, comparing the judges, and validating both against a blind human "
              "sample graded by the author of the standard (Appendix A). The conclusions rest on the contrasts between "
              "conditions, which are stable across judges. C2 replaces the whole document, where retrieval would often "
              "return a mixture, and later models may have seen the decree-law in training."),
        ("h3", "Future Work"),
        ("p", "A mixed condition with both texts; other Member States' transpositions of the same Directive, which "
              "offer up to 27 variants of the design and test the wrong country as well as the wrong level of law; and "
              "an applicability check used as a guardrail, to catch the C2 failure automatically."),
    ]),
    ("6. Conclusion", [
        ("p", "Giving a language model the law transforms its compliance advice on a statute it could not know: coverage "
              "of a lawyer's checklist rose from 27% to 88% and unsupported claims almost disappeared, confirmed by a "
              "second judge and a legal professional's blind grades. A related official text that does not apply gave "
              "no gain and led 94% of answers to apply the Directive as national law, citing provisions that exist."),
        ("p", "A verifiable legal basis shows that the model read something, not that it read the right thing. "
              "Evaluations and guardrails for legal and regulatory advice should test the wrong-document case "
              "explicitly and check applicability, not only existence; our standard and pipeline make that test easy to run."),
    ]),
    ("Code and Data", [
        ("bul", [
            "**Code repository:** " + (REPO_URL or "[link to be added before submission]") + ". The evaluation "
            "pipeline, tests, and the commands that reproduce every table and this report.",
            "**Data/Datasets:** the reference standard (22 questions, 71 items with citations and evidence excerpts), "
            "the official texts of the decree-law and the Directive with their indexes, the prompts and the rubric.",
            "**Other artifacts:** all answers, both judges' marks, the human grades, and the generated tables and figures.",
        ]),
    ]),
    ("Author Contributions", [
        ("p", "B.L. conceived the legal question, wrote the reference standard (questions, checklists, citations, epistemic "
              "statuses and grading notes) and the grading rubric, reviewed the English translation of the decree-law, "
              "and graded the blind sample. S.N. designed and built the evaluation pipeline, ran the experiments and the "
              "analysis, and drafted the Methods and Results. Both authors designed the conditions and metrics, "
              "interpreted the results, and wrote and reviewed the report."),
    ]),
]

REFERENCES = [
    "Cohen, J. (1960). A coefficient of agreement for nominal scales. *Educational and Psychological Measurement*, 20(1), 37-46.",
    "Court of Justice of the European Union (1974). Case 41/74, *Van Duyn v Home Office*, ECLI:EU:C:1974:133. "
    "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:61974CJ0041",
    "Court of Justice of the European Union (1979). Case 148/78, *Criminal proceedings against Tullio Ratti*, "
    "ECLI:EU:C:1979:110. https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:61978CJ0148",
    "Dahl, M., Magesh, V., Suzgun, M., & Ho, D. E. (2024). Large Legal Fictions: Profiling Legal Hallucinations in Large "
    "Language Models. *Journal of Legal Analysis*, 16(1), 64-93. https://doi.org/10.1093/jla/laae003",
    "Decreto-Lei n.º 125/2025, de 4 de dezembro. *Diário da República*, 1.ª série, n.º 234. "
    "https://diariodarepublica.pt/dr/detalhe/decreto-lei/125-2025-962603401",
    "Directive (EU) 2022/2555 of the European Parliament and of the Council of 14 December 2022 on measures for a high "
    "common level of cybersecurity across the Union (NIS 2 Directive). *Official Journal of the European Union*, L 333, "
    "27.12.2022, 80-152. https://eur-lex.europa.eu/eli/dir/2022/2555/oj",
    "Guha, N., Nyarko, J., Ho, D. E., Ré, C., et al. (2023). LegalBench: A Collaboratively Built Benchmark for Measuring "
    "Legal Reasoning in Large Language Models. *Advances in Neural Information Processing Systems 36* (Datasets and "
    "Benchmarks Track).",
    "Lewis, P., Perez, E., Piktus, A., et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. "
    "*Advances in Neural Information Processing Systems 33*.",
    "Longpre, S., Perisetla, K., Chen, A., Ramesh, N., DuBois, C., & Singh, S. (2021). Entity-Based Knowledge Conflicts "
    "in Question Answering. *Proceedings of EMNLP 2021*, 7052-7063. https://doi.org/10.18653/v1/2021.emnlp-main.565",
    "Magesh, V., Surani, F., Dahl, M., Suzgun, M., Manning, C. D., & Ho, D. E. (2025). Hallucination-Free? Assessing the "
    "Reliability of Leading AI Legal Research Tools. *Journal of Empirical Legal Studies*, 22(2), 216-242. "
    "https://doi.org/10.1111/jels.12413",
    "Menezes Cordeiro, A. (2007). *Tratado de Direito Civil Português, I: Parte Geral, Tomo I* (3rd ed., reprint). "
    "Coimbra: Almedina.",
    "Panickssery, A., Bowman, S. R., & Feng, S. (2024). LLM Evaluators Recognize and Favor Their Own Generations. "
    "*Advances in Neural Information Processing Systems 37*. arXiv:2404.13076",
    "Treaty on the Functioning of the European Union, Article 288 (consolidated version). *Official Journal of the "
    "European Union*, C 326, 26.10.2012. https://eur-lex.europa.eu/eli/treaty/tfeu_2012/art_288/oj/eng",
    "Yoran, O., Wolfson, T., Ram, O., & Berant, J. (2024). Making Retrieval-Augmented Language Models Robust to "
    "Irrelevant Context. *International Conference on Learning Representations (ICLR 2024)*. arXiv:2310.01558",
    "Zheng, L., Chiang, W.-L., Sheng, Y., et al. (2023). Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. "
    "*Advances in Neural Information Processing Systems 36* (Datasets and Benchmarks Track). arXiv:2306.05685",
]

LLM_USAGE = [
    "We used Claude (Anthropic) throughout the project. It wrote the evaluation code under our direction, drafted the "
    "checklist items from the decree-law (each was then checked against the official text by B.L., and every citation is "
    "re-checked by script), produced the English reading translation of the decree-law (a random sample of 100 segments "
    "was reviewed by B.L., who found no error), helped B.L. grade answers A16 to A25 of the blind sample, and drafted "
    "this report from the analysis outputs, which we then reviewed "
    "and edited. The models under test and the judges are described in Methods. Every number in the report is produced by "
    "the scripts in the repository from the stored answers and judgments, and we checked the figures in the text against "
    "the generated tables.",
]


def appendix(tables: dict, has_supplementary: bool, has_human: bool = False) -> list:
    items = [
        ("h3", "Limitations and Dual-Use / Ethical Considerations"),
        ("p", "**What the results establish.** For one statute and four models from three families, supplying the "
              "applicable legal text raises checklist coverage from 27% to 88% and nearly removes unsupported claims, while "
              "supplying a related official text that does not apply leaves coverage unchanged and leads most answers to "
              "apply it as national law. The effects are large, hold for every model and for both judges, and are "
              "reproduced by a legal professional's blind grades."),
        ("p", "**What they do not establish.** They do not show how often deployed retrieval systems return the wrong "
              "instrument, how the effect varies across jurisdictions, legal domains or frontier proprietary models, or "
              "whether answers are right on points that rest on later regulation (CNCS Regulation n.º 756/2026 is outside "
              "the reference standard). The uncertainty findings rest on 11 items and are indicative. Absolute levels "
              "without a document vary between judges; the conclusions rest on the contrasts between conditions, which do "
              "not. The study covers one statute, Decreto-Lei n.º 125/2025, in one jurisdiction. The 22 questions and 71 "
              "items were drafted with an LLM and verified by one legal professional, who also graded the blind sample of "
              "25 answers (A01 to A15 alone, A16 to A25 with the help of an AI assistant); there is no second human grader."),
        ("p", "**Dual use: informing or manipulating.** The central finding could be used to manipulate rather than "
              "inform: supplying a related but inapplicable official text makes legal advice look authoritative, because "
              "every citation checks out, for example to persuade a company that it has no duty the national law imposes "
              "(as in the blind-sample answer on the cybersecurity officer) or that a different regime of deadlines and "
              "fines applies. We judge the risk low and the disclosure worth it: the finding points to a simple defence, "
              "checking that the cited instrument governs the question, we publish no advice tool, and the materials we "
              "release (questions, checklists, answers, grades) are built to test models, not to advise companies."),
        ("p", "**Personal data.** No personal data about third parties was collected or used: the questions concern a "
              "public law, and the official texts and the model outputs are public or generated. The blind grading records "
              "only the grader's legal marks and notes. The company linked to the pre-existing work is not named in this "
              "report, in the repository, in the reference standard or in the prompts."),
        ("p", "**Not legal advice.** The questions, checklist items, model answers and results serve to evaluate language "
              "models. They are not legal advice and should not be used as such. The checklist is one legal professional's "
              "reading of the official text. The English translation of the decree-law is unofficial; in case of doubt, "
              "the Portuguese text published in the Diário da República shall be consulted."),
        ("p", "**Pre-existing work.** Before the sprint (18 to 30 October 2026), B.L. built, with Claude, an interactive "
              "web page on NIS2 compliance for a mid-sized Portuguese IT services company. It is in Portuguese, it was not "
              "paid and is not published. It was a source of topics (every one of the 22 questions turns on a point the page "
              "also discusses) and of the four status labels (verified, inferred, to confirm, proposal). The questions, "
              "checklist items and citations were written and checked against the official text during the sprint: no "
              "question and 2 of the 71 items share their opening wording with the page. The page was never given to a "
              "model or to the judges. Everything else in this report was done between 13 and 15 November 2026."),
        ("h3", "Prompt"),
        ("p", "The system instruction and the request are the same in all conditions; only the document block changes. "
              "Original Portuguese, with our English gloss."),
        ("mono", [
            "*System:* É um assistente que ajuda empresas em Portugal a perceber as suas obrigações legais em matéria de "
            "cibersegurança. (You are an assistant that helps companies in Portugal understand their legal obligations on "
            "cybersecurity.)",
            "*Document block, C1:* Segue-se o texto oficial do Decreto-Lei n.º 125/2025, de 4 de dezembro (o decreto-lei, o "
            "regime jurídico da cibersegurança aprovado em anexo e os anexos I a III), publicado no Diário da República. "
            "[full text]",
            "*Document block, C2:* Segue-se o texto oficial, em português, da Diretiva (UE) 2022/2555 do Parlamento Europeu e "
            "do Conselho, de 14 de dezembro de 2022 (Diretiva SRI 2), publicado no Jornal Oficial da União Europeia. [full text]",
            "*Request:* Pergunta de uma empresa em Portugal, sobre o direito português em vigor: [question]. Responda de "
            "forma completa e indique a base legal (diploma, artigo, número e alínea) do que afirmar. (Question from a "
            "company in Portugal, about Portuguese law in force: [question]. Answer in full and give the legal basis "
            "(statute, article, paragraph and point) for what you state.)",
        ]),
        ("h3", "Example of a question and its checklist"),
        ("p", "Question L1-07 (in English): \"Can an entity ask not to be fined while it adapts to the new regime? Until "
              "when?\" Checklist: (a) *verified*: yes, by a reasoned request, on the ground that no internal adaptation "
              "procedure exists, exemption from the fines in arts. 61.º, n.º 2, and 62.º, n.º 2 (art. 65.º); (b) "
              "*verified*: \"for 12 months from the entry into force\" of the decree-law (art. 65.º); (c) *inferred*: "
              "the decree-law entered into force 120 days after publication, on 3 April 2026, so the 12 months end on "
              "3 April 2027 (art. 11.º of the decree); (d) *inferred*: the exemption can be requested until 3 April 2027. "
              "The doubt in (d), kept in the grading note: the 12 months may be the period to make the request, or the "
              "period whose facts the exemption covers; a stricter day count (Civil Code art. 279.º) would give 4 April 2027. "
              "With the decree-law, answers stated (d) as certain 8 times of 9."),
        ("h3", "Results per model"),
        ("md_table", ("5. Per model", 0, "**Table A1.** Checklist coverage per model and condition (judge qwen3.8-27b; "
                      "95% bootstrap intervals over questions). qwen3.8-27b is graded by itself; gemma-4-26b-a4b-it, where shown, "
                      "is the supplementary model.", [3060, 2100, 2100, 2100], 18)),
        ("md_table", ("5. Per model", 1, "**Table A2.** Answers with at least one unsupported claim, per model and condition.",
                      [3060, 2100, 2100, 2100], 18)),
        ("md_table", ("5. Per model", 2, "**Table A3.** Answers with jurisdiction confusion, per model and condition.",
                      [3060, 2100, 2100, 2100], 18)),
        ("h3", "Second judge"),
        ("md_table", ("3. Second judge", 0, "**Table A4.** The main table graded by the second judge, gemma-4-31b-it, with "
                      "its own answers left out (qwen3.5-397b, qwen3.8-27b, deepseek-v4-flash; 594 answers).",
                      [3660, 1900, 1900, 1900], 18)),
        ("h3", "Uncertain items"),
        ("md_table", ("6. Uncertain items", 0, "**Table A5.** What the answers did with the 11 uncertain checklist items: "
                      "counts of item marks, three main models, judge qwen3.8-27b.", [1500, 1200, 1700, 1700, 1500, 1760], 18)),
        ("md_table", ("6. Uncertain items", 1, "**Table A6.** The same, by item, with the decree-law (C1). Nine marks per "
                      "item: three models, three repetitions.", [1800, 1800, 1920, 1920, 1920], 18)),
        ("h3", "Citations"),
        ("md_table", ("7. Citations", 0, "**Table A7.** Deterministic citation check, all four models, 792 answers. A "
                      "citation is checked against the text the answer attributes it to.",
                      [900, 900, 1100, 1300, 1300, 1300, 1300, 1260], 16)),
        ("md_table", ("7b. Which national law", 0, "**Table A8.** Which national law the answers rest on (text search, all "
                      "four models). The decree-law repeals Lei n.º 46/2018 and Decreto-Lei n.º 65/2021.",
                      [1100, 1100, 2200, 2700, 2260], 17)),
    ]
    if has_supplementary:
        items += [
            ("h3", "Supplementary model"),
            ("p", "A fifth model, gemma-4-26b-a4b-it, was run after the main result was complete, with the same "
                  "settings, and graded by both judges. It reproduces the pattern of the four core models."),
            ("md_table", ("10. Supplementary", 0, "**Table A9.** The main table for the supplementary model "
                          "gemma-4-26b-a4b-it (judge qwen3.8-27b).", [3660, 1900, 1900, 1900], 18)),
        ]
    if has_human:
        items += [
            ("h3", "Blind sample graded by the author of the standard"),
            ("p", "25 answers drawn before any grading (C0: 8, C1: 9, C2: 8), graded blind with the rubric. The grader "
                  "entered the answer-level marks on the first checklist row of 15 answers; they were moved to the answer "
                  "row before scoring, and no mark was changed (scripts/import_human_grades.py)."),
            ("hmd_table", ("1. By condition", 0, "**Table A10.** The grader and the two judges on the same 25 answers.",
                           [3000, 1860, 1500, 1500, 1500], 18)),
            ("hmd_table", ("2. The legal basis", 0, "**Table A11.** The legal basis each answer rests on, as named in the "
                           "grader's notes (our coding of her notes; answers can fall under more than one row).",
                           [5160, 1400, 1400, 1400], 18)),
            ("p", "In her notes the grader also revised one checklist item: for managed service providers the three-month "
                  "rule of art. 35.º, n.º 4 displaces the general 30-working-day rule as the special rule, so the overlap "
                  "marked as inferred in L2-01 e is in her view settled. The item was kept as frozen."),
        ]
    items += [
        ("h3", "English translation of the decree-law"),
        ("p", "The models and the judges worked on the official Portuguese text only. For readers who do not read "
              "Portuguese we keep an English translation of the decree-law in the repository. It was produced with an LLM, "
              "segment by segment (1,149 segments), checked by script for completeness, structure and numbers, and reviewed "
              "by one legal professional on a sample: 12 segments chosen by type and 100 drawn at random from the 883 "
              "running-text segments. No error of any category was found in the sample. This is a single-reviewer check, "
              "not inter-rater agreement; with no serious error in 100 random segments, fewer than about 3% of segments "
              "have one (95% bound)."),
    ]
    items += [
        ("h3", "Legal Epistemics: What Law Requires and What It Only Permits"),
        ("p", "A compliance question usually asks whether a company must do something. In law, the answer depends on the "
              "kind of legal situation that the provision creates, not only on whether the text mentions an action. The "
              "scheme below is B.L.'s own summary of the reference legal theory in Menezes Cordeiro (2007), vol. I, "
              "§§ 20-24, pp. 302-361."),
        ("p", "Active situations (subjective right, potestative right, power, exception) place effects in the hands of the "
              "holder's own will; they rest on permissive norms or on norms that confer a power. Passive situations "
              "(obligation or duty, subjection, burden or onus, generic duty, functional duty), on the other hand, come "
              "from norms that forbid or impose conduct."),
        ("p", "An obligation (*obrigação*) is the comprehensive and relative figure: a legal bond by which one person is "
              "bound to another to perform a prestation. A duty (*dever*) is the analytical figure: a legal bond to "
              "something. A subjective right and the obligation that faces it are not alternatives: they are two "
              "situations in one legal relationship, the right on the active side and the obligation on the passive side. "
              "The conduct owed can be an act (*facere*), an abstention (*non facere*) or toleration (*pati*). A person is in "
              "subjection (*sujeição*) when another can change their legal sphere unilaterally and they cannot prevent it."),
        ("p", "Question L1-06 shows how a situation is linked to a sanction: (1) A norm imposes conduct, so the company is "
              "in a passive situation, a duty: for example, to notify incidents (arts. 40 to 44) or to inform service "
              "recipients (art. 48). (2) Breaching these duties is a very serious offence (art. 61(1)). (3) The fine "
              "follows: for important entities from €1,250 to €7,000,000, or a maximum of not less than 1.4% of worldwide "
              "annual turnover, whichever is higher (art. 61(2)); negligence halves the limits (art. 64). (4) The "
              "authority's power to impose the fine is an active situation, and the company is in subjection to it. (5) The "
              "company has an active situation of its own: it may ask, on reasoned grounds, for exemption from the fines "
              "for 12 months (art. 65, question L1-07). That is a permission, not a duty."),
        ("p", "**Other examples.** In a corporate group each company may have a contact point under an officer common to "
              "the group (art. 31(7), item L1-03 d): a faculty, not a duty. Before the CNCS qualifies an entity, the entity "
              "may respond within 10 working days (Regulation 756/2026, art. 9(2)); if it does not, the CNCS decides "
              "without its response (art. 9(4)): a burden (*ónus*), not a duty."),
        ("p", "The implication of legal theory for evaluation is that an answer that turns a faculty into a duty, or the "
              "reverse, makes a legal error, even if every article it cites exists. Telling these situations apart is part "
              "of reading the law correctly, and it is a test that models can be given explicitly."),
    ]
    letters = iter("ABCDEFGHIJKLMNOP")
    items = [(k, f"{next(letters)}. {v}") if k == "h3" else (k, v) for k, v in items]
    return items
