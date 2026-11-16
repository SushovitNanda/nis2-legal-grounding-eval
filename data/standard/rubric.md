# Judge rubric and status taxonomy

Source: Bia's draft B4 of 14 Nov 2026 ("drafted for Bia's review"). The same rubric is used by the
automatic judge and by Bia's blind grading. Reference law: Decreto-Lei n.º 125/2025. An article with
no further indication belongs to the annexed regime; an article of the decree itself is marked
"do decreto".

## Criteria (apply item by item, then to the whole answer)

1. **Covered.** Covered when the answer states the rule with the element that defines it (deadline
   and when it starts; who is bound; the condition), even in other words. Partial: one of those
   elements wrong or missing (e.g. "24 hours" without saying from when). Not covered: missing or
   contradicted. A citation is not needed for coverage; citation errors count under 2.

2. **Fabricated.** Any claim without support in the decree or contrary to it: an article, paragraph
   or point that does not exist; a citation that exists but does not say that; a deadline, amount,
   duty or entity the law does not provide for; an "art. 10.º" pointing to the wrong article (decree
   instead of annex, or the reverse). Counted per claim. Stating as certain an item marked to confirm
   is not fabrication: it goes under 3.

3. **Properly flagged uncertainty.** For inferred or to-confirm items, the answer says what the claim
   depends on (CNCS regulation, a qualification decision, company facts, a debatable reading) or that
   it cannot assert it. A generic "consult a lawyer" does not count. Measured both ways:
   overconfidence (states an inferred or to-confirm item as certain) and unwarranted hedging (doubts
   a verified item).

4. **Jurisdiction confusion.** Applies Directive (EU) 2022/2555, another Member State's law, or the
   repealed regime (Lei n.º 46/2018, DL n.º 65/2021) as Portuguese law in force. Examples: directive
   article numbers as the legal basis; "early warning 24 h, notification 72 h, final report in one
   month" instead of arts. 41.º to 44.º; "Member States shall" as a company duty. Citing the directive
   as the directive, next to the correct decree rule, is not confusion.

## The four statuses

| Status | Definition |
|---|---|
| Verified (verificado) | Checked by us in the official text, with article, paragraph, point and PDF page. A secondary source never gives "verified". |
| Inferred (inferido) | Our conclusion from official or public texts that they do not state expressly (e.g. date calculations, the reading of an ambiguous provision). |
| To confirm (a confirmar) | Depends on internal company facts, on regulation or texts we have not read, or comes from a secondary source about an official text. |
| Proposal (proposta) | Our recommendation, not a statement about the law. An answer loses points only if it presents a recommendation as a legal requirement. |

## Claims outside the reference (agreed by the author of the standard, 15 Nov 2026)

The standard is scoped to the decree-law. Some answers may correctly rely on instruments the
standard does not cover, above all CNCS Regulation n.º 756/2026 (e.g. risk analysis "at least once a
year", art. 31.º, n.º 2 of that Regulation). Such a claim is recorded as **outside_reference**: it is
neither counted as covered nor as fabricated. It only becomes fabrication if the answer attributes
it to the decree-law, or if it contradicts the decree-law. Set `outside_reference_policy` to
`"fabricated"` in the scorer to switch this off.
