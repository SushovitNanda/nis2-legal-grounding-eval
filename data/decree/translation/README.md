# English translation of Decreto-Lei n.º 125/2025 (unofficial)

| File | What it is |
|---|---|
| `DL-125-2025-pt-en-proposed-translation.pdf` | The bilingual table, 91 pages: source page, Portuguese as published, proposed English translation, one row per paragraph or point (1,149 segments). Received 14 Nov 2026. |
| `DL-125-2025-en-proposed.txt` | The English column alone, extracted by `scripts/extract_decree_translation.py`. All 100 article headings are present and in order (11 of the decree-law, 87 of the regime, 2 of Annex III). |
| `translation-review-signed-2026-11-14.pdf` | The reviewer's signed method statement and her review of a sample of the translation, 16 pages. Received 15 Nov 2026. **Git-ignored**: its signature block carries her full name and identification number. Publish only with her consent, or as a version without the signature block. |

**Status.** Unofficial. Produced with AI (Claude), segment by segment, from the published text, then
checked by script and reviewed on a sample by one legal professional. Not reviewed by a translator. Only the Portuguese text
in the Diário da República is official.

## What the review shows (from the signed statement)

- **Checks by script, whole text:** every Portuguese segment has an English segment (1,149 of 1,149);
  the leading marker of each segment ("1 -", "a)", "i)") is the same in both languages; the set of
  numbers in each segment (articles, paragraphs, deadlines, dates, amounts, percentages) is the same
  in both, after comparing 19 euro amounts by value because their format differs.
- **Human review of a sample:** sample A, 12 segments chosen by type (definitions, notification
  deadlines, sanctions, cross-references, authority and entity terms, provisions of the decree-law
  itself); sample B, 100 segments drawn at random (seed 20261114) from the 883 running-text segments.
  One segment is in both, so 111 distinct segments.
- **Scale:** 10 no error; 8 grammar or style only; 6 wrong technical term, same legal effect; 4 a
  condition, proviso or negation lost; 2 legal effect changed.
- **Result:** every reviewed segment scored 10. No segment in either sample has an error of any category.

## How to state this in the report

- It is a **single-reviewer accuracy check, not inter-rater agreement.** The statement says so itself:
  "No second reviewer; no inter-rater agreement." Do not call it agreement, and do not confuse it with
  the judge-versus-human agreement on the model answers (Cohen's kappa), which is a different table.
- What the random sample supports: 0 serious errors in 100 random segments puts the share of
  running-text segments with a serious error below about 3% (95% upper bound, 1 - 0.05^(1/100) = 2.95%).
  It does not show that there are none.
- The reviewer also commissioned the translation and wrote the reference standard; she is not
  independent of the project.
- Not covered by the review: article and chapter titles, the tables of Annexes I to III, and segments
  shorter than 25 characters (left out of the pool the random sample was drawn from).
- Things to fix in the statement before it goes in an appendix: points 3.1 and 4.1 repeat point 2.3
  word for word; point 4.5 says "all 112 segments" where 4.2 says 111 distinct segments.

## What it is used for

- **Reading aid.** For anyone on the team or reading the report who does not read Portuguese: to
  follow a provision the checklist cites, or to read a judge output against the rule it refers to.
- **Quotations in the report.** A provision can be quoted in English next to the Portuguese, marked
  "our translation; a random sample of 100 segments was reviewed by a legal professional, no errors found".

## What it is not used for

- **Not a model context in C0, C1 or C2.** C1 gives the models the official Portuguese text. The
  result we report is about the official text.
- **Not seen by the judge.** The judge reads the official Portuguese text.
- **Not a source for the standard.** Checklist citations are checked against the Portuguese text only.

## Possible stretch use

A robustness run in English (`--lang en`): English questions, this translation as the document in
place of the Portuguese decree, and the official English directive in C2. It would show whether the
results depend on the language. With the review above this is now defensible, with the caveat that
the document is a translation checked on a sample. It needs a runner option for an English decree
that does not exist yet.

## Known issues

- The Portuguese column of the PDF contains private-use glyphs where the official PDF's font hides
  the letters "i" and "v" (273 occurrences). The English column is clean. Use
  `data/decree/DL-125-2025.txt` for the Portuguese text, never this PDF.
- Where the original has typographical errors, the translation follows them (see the PDF's first page).
- Publication: agreed by the reviewer, B. Lourenço (16 Nov 2026), marked unofficial and not reviewed by a translator.
