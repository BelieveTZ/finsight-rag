# Failure Analysis

This record includes unsuccessful development runs. A refusal can prevent a bad
answer from reaching the user while still counting as a failed answerable question.
Checks for strings and numbers are not a semantic correctness guarantee.

## Retrieved Evidence Is Not Necessarily Supplied Evidence

The [first qualitative retrieval check](../artifacts/demo/20260919T062000561673Z-fact-retrieval.json)
ranked the supplier-risk page eighth with hybrid retrieval, but the evidence byte
budget excluded it. Dense did not retrieve the annotated page in its top ten.
The fact-only branch-champion policy promotes each branch's first result within the
already returned top ten. Its [CPU follow-up](../artifacts/demo/20260919T062400022446Z-fact-retrieval.json)
included the page. This exposed two-question experiment does not establish broad
improvement; lexical champions can also be irrelevant.

## A Correct Number With the Wrong Citation Still Fails

The [statement-first experiment](../artifacts/rag/20260919T051933127591Z.json) dropped
from 8/9 to 7/9 on exposed 3M checks. The desired statement entered context, but the
model still selected distracting pages or units. Stable promotion alone was not
enough. The subsequent filtered policy enforces an explicit statement constraint
using headings in retrieved candidates only. It does not scan gold pages as a fallback.

## The Validator Can Also Be Wrong

In the [first filtered run](../artifacts/rag/20260919T063902498787Z.json), the model
returned 8.738 USD billions from the correct 3M balance sheet, PDF 58. Validation
rejected the split title `Consolidated Balance Shee t`. Selection and validation
were using different title rules. A shared full-line, whitespace-normalized heading
check fixed this mismatch; narrative references still fail. The
[rerun](../artifacts/rag/20260919T064217520439Z.json) reached 9/9 on these exposed cases.

## Missing Units and Wrong Scaling

The [initial portfolio generation run](../artifacts/portfolio/20260919T064443995840Z-development-rag.json)
contains several distinct errors:

- Dense 3M revenue proposed 31,500 million while citing a 12.3-billion industrial
  segment excerpt. Numeric evidence validation rejected it.
- Dense 3M dividends quoted the correct 3.193 billion, but the numeric field became
  3,193,000 million. The factor-of-1,000 error was rejected.
- Hybrid PepsiCo operating cash flow returned the correct 10,811-million value from
  a summary without explicit source units in that chunk. Validation refused it.
  Correct digits alone do not establish the required unit.
- Hybrid PepsiCo assets gave the right value but selected a chunk whose body did not
  contain its quote. Another chunk on the same page is not the cited chunk.

The development prompt follow-up asks for self-contained units and a quote in the
exact cited chunk. Validation rules were not relaxed, and the original failures
remain in their original denominator.

## A Real Quote Can Support the Wrong Metric

Both methods in that same initial run answered the PepsiCo **net income attributable
to PepsiCo** question with 8,978 million, which is total net income including
noncontrolling interests. The requested amount is 8,910 million. The quote exists,
the year and unit are correct, and all structural checks pass, yet the answer is
wrong. The source is PDF 62, with the two distinct rows visible together.

This is why the acceptance review checks row meaning, not only exact-match strings.
The prompt follow-up explicitly requests the entire metric qualifier. It is a
development intervention, not evidence that every future semantic error is blocked.

## Qualitative Scope Error

The [first six-case model demonstration](../artifacts/demo/20260919T065350455654Z-generation.json)
passed all six automatic checks but only five source reviews. The FLNA answer's
quote continued into the Quaker Foods section and listed another division's
products, despite citing the correct page. The model's separate paraphrase was
plausible; the delivered quote was not an adequate answer. This result is **not**
six-of-six accepted demonstrations. The fact-prompt follow-up requests short,
complete, entity-specific sentences without crossing sections. Numeric scoring
and quote checks remain unchanged.

## Final-Set Failures, Not Retuned

The [frozen final run](../artifacts/portfolio/20260919T070257595016Z-final-rag.json)
was retained without pipeline changes. The [complete source review](SOURCE_REVIEW.md)
includes every answer and refusal, not only favorable examples.

- Dense AMD capex selects a PP&E balance of 1,513 instead of purchases of 450 million.
  Retrieval misses the labeled cash-flow page, and the semantic metric mismatch
  survives structural validation.
- Both AMD PP&E answers find the right number but fabricate a contiguous quote by
  joining text. Quote validation turns them into false refusals.
- Dense CVS income selects 3.16 basic earnings per share. The table header says
  millions **except per-share amounts**; the numeric guard does not resolve that
  row-level exception. This is an incorrect delivered answer, not a successful guard.
- Dense CVS assets, PP&E, capex and operating cash flow are refused. Page recall
  alone overstates usable evidence for the assets case: the page is present but
  the target row is absent from the returned chunk.
- Hybrid CVS assets matches the expected amount by citing liabilities plus equity.
  It is not counted as direct extractive support, despite numeric success.
- Hybrid CVS capex mistakes a 2021 impaired-asset fair value for 2022 purchases.
  A year somewhere in a chunk is not enough to attach that year to every sentence.
- Hybrid CVS PP&E returns a real note amount including held-for-sale assets, unlike
  the fixed balance-sheet label. This exposes an ambiguous question definition;
  preserve the original score and record the footnote, rather than relabeling the
  result after the fact.

## Interpretation

Failures can originate in extraction, retrieval, context selection, generation,
validation or evaluation labels. Diagnose the actual stage before changing models.
Retain fixed-label retrieval results even when source review finds a valid
alternative page. Report service failures separately from evidence refusals, and
report false refusals against all answerable questions, not only delivered answers.
