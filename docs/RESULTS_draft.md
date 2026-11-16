# Results (draft, 15 Nov 2026)

Every number below comes from `results/full/RESULTS_tables.md`, which `scripts/results_tables.py`
builds from the scored run; the human-grader figures come from `results/full/blind/human_results.md`
and `agreement.<judge>.md`.

**Data.** The four core models answered each of the 22 questions under each of the three conditions
three times: 792 answers, none missing. Both judges graded all 792. Unless stated otherwise, results
are for the three models that are not the main judge (qwen3.5-397b, gemma-4-31b-it,
deepseek-v4-flash; 594 answers), graded by qwen3.8-27b. Percentages are means over the 22 questions,
with 95% bootstrap intervals over questions in brackets.

## Table 1. Main result

| | C0 question only | C1 with the decree-law | C2 with the directive instead |
|---|---|---|---|
| Checklist coverage | 27% [19, 35] | 88% [81, 94] | 26% [17, 38] |
| Answers with at least one unsupported claim | 95% [86, 100] | 10% [5, 17] | 85% [77, 92] |
| Unsupported claims per answer | 3.9 [3.4, 4.4] | 0.1 [0.1, 0.2] | 2.9 [2.4, 3.4] |
| Answers with jurisdiction confusion | 58% [46, 68] | 0% | 94% [90, 97] |
| Says the decree does not settle the point (3 questions) | 30% [11, 56] | 100% | 11% [0, 22] |
| Says the text given is not the Portuguese law | 0% | 0% | 14% [9, 19] |

Figure 1 (`results/full/fig_main_result.png`) shows four of these rows.

## Findings

**1. With the decree-law in front of them, the models answer from it.** Coverage rises from 27% to
88% (paired difference per question +61 points [+51, +69]). The share of answers containing at least
one unsupported claim falls from 95% to 10% (-85 points [-93, -73]). No answer confused the directive
with the national law. Of the 4,954 citations to the decree-law in these answers (all four models),
87 (1.8%) point to a provision that does not exist.

**2. Without the text, the models answer anyway, from the wrong sources.** Asked without any document what
Decreto-Lei n.º 125/2025 is, all four models said they did not know it. Asked a compliance question,
they answered: 95% of the answers contain at least one unsupported claim, 3.9 on average. None of the
264 answers without a document names Decreto-Lei n.º 125/2025. Instead, 154 (58%) rest on Lei n.º
46/2018 or Decreto-Lei n.º 65/2021, the regime that the decree-law repealed, and 153 (58%) name some
other statute dated 2023 to 2026 as the transposition. Of about 3,200 citations in these answers,
2,498 (78%) are to instruments other than the decree-law and the directive.

**3. Given the directive instead, the models apply it as Portuguese law.** Coverage is the same as
with no text at all (26% against 27%; difference 0 points [-6, +6]): the directive does not carry the
national rules the questions ask about. But 94% of these answers show jurisdiction confusion, against
58% with no text, and only 14% say that the text they were given is not the Portuguese law. The
citations are real: of 4,157 citations to the directive, 132 (3.2%) do not exist. The error is in
applying the directive, not in inventing it: of the 168 answers with an unsupported claim under C2,
157 are also marked for jurisdiction confusion, and most of those claims are rules of the directive
stated as Portuguese law. An answer of this kind looks well grounded and is wrong
about the law in force.

**4. Uncertainty is flagged only when the text is there, and then about half the time.** The
standard has 11 items that are uncertain (inferred, or depending on regulation or facts not in the
decree). Without the decree-law, or with the directive, the answers almost never reach them (93% of
marks "not addressed" in both conditions). With the decree-law, of 99 marks, 42 flag the doubt, 29
state the point as certain and 28 do not address it. The pattern by item is consistent: where the
decree itself says a matter is left to regulation, the models say so (L2-10 b and L2-11 b: flagged 9
times of 9). Where the answer requires a date calculation or a reading of an ambiguous provision,
they state the result as certain (L1-07 d: 8 of 9; L1-03 c: 6 of 9).

**5. On the three questions the decree-law does not answer, the text makes the models say so.** With
the decree-law, every answer says the decree does not settle the point (27 of 27), and 4% contain a
unsupported claim. Without it, 30% say so and every answer contains an unsupported claim. With the
directive, 11% say so.

**6. The pattern is the same for every model.** Coverage with the decree-law ranges from 82%
(gemma-4-31b-it) to 95% (qwen3.8-27b, graded by itself); without it, from 18% to 32%. The share of
answers with an unsupported claim under the decree-law is between 5% and 14% for all four. The models
differ most under the directive: gemma-4-31b-it has an unsupported claim in 62% of its answers there,
the other three in 86% to 100%.

## Robustness

**Second judge.** gemma-4-31b-it graded all 792 answers again with the same prompt. Leaving out its
own answers, it gives coverage 17% / 88% / 27% and answers with an unsupported claim 98% / 13% / 97%
for C0 / C1 / C2. For the two models that are neither judge (qwen3.5-397b, deepseek-v4-flash), the
two judges give coverage 26% / 90% / 27% and 20% / 86% / 30%. The conclusions do not depend on the
judge. The levels without the decree-law do: the two judges differ by up to 10 points on coverage
under C0, and on jurisdiction confusion under C0 (58% against 88%).

## Table 2. Agreement between the two judges (792 answers)

| Mark | Cohen's kappa | Raw agreement |
|---|---|---|
| Item coverage, three levels (linear-weighted) | 0.83 | 85% |
| Uncertainty mark on uncertain items | 0.67 | 87% |
| Answer has an unsupported claim | 0.86 | 93% |
| Jurisdiction confusion | 0.82 | 91% |
| Says the decree does not settle the point | 0.66 | 92% |

Agreement is lower within the condition without a document (coverage kappa 0.63; jurisdiction
confusion 0.39), where the answers are furthest from the checklist and the judges have most to
interpret. Without the two judges' own answers (396 answers) the figures are close to the table
(coverage 0.80, unsupported claim 0.92).

**All four models.** Including the main judge's own answers changes little: coverage 24% / 89% / 26%,
answers with an unsupported claim 96% / 11% / 85%.

**Repetitions.** The mean standard deviation of coverage across the three repetitions of a cell is
0.10 without a document, 0.04 with the decree-law and 0.06 with the directive.

**Judges against the human grader.** The author of the standard graded a blind sample of 25 answers
(C0: 8, C1: 9, C2: 8) with the same rubric, without seeing model, condition or the judges' marks.

| Mark | qwen3.8-27b vs grader | gemma-4-31b-it vs grader | n |
|---|---|---|---|
| Item coverage, three levels (linear-weighted kappa) | 0.71 (78%) | 0.64 (74%) | 85 items |
| Answer has an unsupported claim | 0.64 (84%) | 0.71 (88%) | 25 answers |
| Jurisdiction confusion | 0.92 (96%) | 0.92 (96%) | 25 answers |
| Uncertainty mark on uncertain items | 0.22 (50%) | 0.22 (50%) | 8 marks: too few |

Graded by her alone, the sample shows the same pattern: coverage 12% / 88% / 40%, an unsupported claim
in 8 of 8 / 2 of 9 / 8 of 8 answers, jurisdiction confusion in 7 / 0 / 8 (C0 / C1 / C2). She graded
A01 to A15 alone and A16 to A25 with the help of an AI assistant; on A01 to A15 agreement is as high
(coverage 0.67 and 0.63; unsupported claim 0.86 for both; jurisdiction 0.87 and 1.00). In her notes,
all 16 answers without the decree-law rest on a wrong legal basis (the Directive in 9, a statute that
is not the transposition in 8, the repealed Lei n.º 46/2018 in 4; our coding of her notes), and all 9
with it rest on the decree-law. The disagreements are of two kinds: she credits content right in
substance under a wrong legal basis (her C2 coverage 40% against 24% and 34%), and she catches claims
about CNCS Regulation 756/2026, which the judges, seeing only the decree-law, cannot.

## Supplementary

- **A fifth model (gemma-4-26b-a4b-it)**, run after the main result was complete (198 answers, judge
  qwen3.8-27b), shows the same pattern: coverage 19% / 81% / 24%, answers with an unsupported claim
  95% / 18% / 65%, jurisdiction confusion 80% / 0% / 100% for C0 / C1 / C2. Full table: section 10 of
  `RESULTS_tables.md`.
- **Designed for follow-up work:** a pushback condition and a condition adding a scheme of legal
  categories to the decree-law.

## What the results do not show

- Levels under C0 depend on the judge (see above); the contrasts do not.
- Uncertainty rests on 11 items in 9 questions; the interval on "properly flagged" under the
  decree-law is wide (48% [24, 73]).
- "Unsupported claim" (the rubric's "fabricated": no support in the decree-law, or contrary to it) is the judge's mark. Agreement between the two judges on it is high (kappa
  0.86), but both are language models and both are test models; the human grades are the only
  independent check.
- Three of the four models have documented training cutoffs before the decree-law was published
  (4 December 2025); the fourth has no published cutoff. None showed knowledge of the decree without
  the text.
- One statute, one jurisdiction, 22 questions written by one author.
