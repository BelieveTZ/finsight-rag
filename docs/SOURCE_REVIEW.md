# Source Review

Review method: compare delivered responses with rendered original PDF pages and
extracted text, checking entity, metric, fiscal column, currency, scale and source
location. This is an implementation-stage review, not an independent or blinded
assessment. The automated checker is not the semantic judge. Original labels and
run artifacts are unchanged. PDF pages below are one-based file pages.

Each numeric answer contains one factual value and one citation. Refusals make no
numeric claim. Citation support below means support for the **requested fact**,
not merely that the quoted words appear somewhere in the document.

## Development Numeric Answers

Run: [20260919T064925054509Z](../artifacts/portfolio/20260919T064925054509Z-development-rag.json).
This is exposed development data after a prompt follow-up, not final accuracy.

| Case | Dense | Hybrid | Source finding |
| --- | --- | --- | --- |
| 3M capex | Supported, p60 | Supported, p60 | 2018 PP&E purchases: spending magnitude 1,577 million |
| 3M net PP&E | Supported, p58 | Supported, p58 | 8,738 million = 8.738 billion; net, not gross PP&E |
| 3M revenue | **Unsupported**, p33 | Supported, p14 | Dense returns 12,300 million industrial-segment sales, not 32,765 million company revenue |
| 3M dividends | Supported, p48 | Supported, p48 | 3.193 billion converts to 3,193 million; 2018, not the later dividend announcement |
| 3M attributable income | Supported, p14 | Supported, p14 | 2018 parent-attributable income 5,349 million |
| 3M assets | Supported, p58 | Supported, p14 | 2018 year-end assets 36,500 million |
| PepsiCo revenue | Supported, p62 | Supported, p62 | 2022 net revenue 86,392 million |
| PepsiCo attributable income | Supported, p62 | Supported, p62 | 8,910 million attributable to PepsiCo, distinct from 8,978 total income |
| PepsiCo assets | Supported, p66 | **False refusal** | Correct raw value, but quote is not in the cited chunk body; refusal contains no delivered citation |
| PepsiCo net PP&E | Supported, p66 | Supported, p66 | 2022 net PP&E 24,291 million |
| PepsiCo capex | Supported, p64 | Supported, p64 | Capital spending magnitude 5,207 million |
| PepsiCo operating cash flow | Supported, p64 | Supported, p64 | Net cash provided by operating activities 10,811 million |

Both methods: 11/12 answer correctness. Dense: 11/12 delivered citations support
the requested fact; hybrid: 11/11. Missing citations on delivered factual answers:
0 for either method. False refusals: dense 0/12, hybrid 1/12. The dense wrong-metric
answer passes automated structure/source checks; do not claim hallucinations are
eliminated. Gold-page Recall@10 remains 9/12 and 10/12 respectively, even when the
alternative 3M pages 14 and 48 genuinely support answers.

Both methods correctly refuse all three development probes: two scope refusals
(wrong year/company, without model generation) and one model refusal for the
undisclosed Microsoft customer revenue. Full-report absence checks are documented
in [corpus provenance](CORPUS.md); this does not imply zero sales to that company.

## Six Demonstrations

Accepted run: [20260919T065722467425Z](../artifacts/demo/20260919T065722467425Z-generation.json).
All six manifest cases were run, not selected after observing success. Automatic
checks and source review are separate; this page supplies the latter. The earlier
[failed business excerpt](../artifacts/demo/20260919T065350455654Z-generation.json)
remains available and is not counted as an accepted six-of-six run.

| Case | Delivered result | Review |
| --- | --- | --- |
| 3M capex | 1,577 USD millions, PDF 46 | Valid alternative cash-flow table, with 2018 and millions headers. This question does not require the formal statement page 60. Original annotation remains p60. |
| PepsiCo operating cash flow | 10,811 USD millions, PDF 64 | Correct operating-activities row and 2022 column, not investing/financing cash flows |
| FLNA products | Original excerpt, PDF 5 | FLNA convenient foods, dips and snack chips. The accepted quote ends before the Quaker Foods section; source section and entity agree. |
| Limited-supplier risk | Original excerpt, PDF 17 | Directly identifies limited/sole sources and seasonal shortages. Does not claim a quantified loss or current disruption. |
| 3M FY2024 revenue | Scope refusal | The selected 2018 report cannot establish actual 2024 revenue; no model call |
| PepsiCo Microsoft revenue | Model refusal | No disclosed customer-specific amount; no invented amount or citation |

Accepted demonstrations: 6/6; answered-citation support: 4/4; missing citations on
delivered factual answers: 0. These are exposed development demonstrations, not
held-out accuracy or proof of general qualitative QA quality.

## Frozen Final Evaluation

Run: [20260919T070257595016Z](../artifacts/portfolio/20260919T070257595016Z-final-rag.json).
The frozen pipeline was not changed or rerun in response to these results.

| Case | Dense | Hybrid | Review finding |
| --- | --- | --- | --- |
| AMD revenue | Supported, p68 | Supported, p54 | 2022 total company revenue 23,601 million; p68 is a valid alternative segment-reconciliation total |
| AMD income | Supported, p55 | Supported, p55 | Net income 1,320 million, not comprehensive income 1,282; valid alternative statement |
| AMD assets | Supported, p56 | Supported, p56 | Total assets 67,580 million, correct 2022 column |
| AMD net PP&E | False refusal | False refusal | Raw 1,513 value correct, but neither quote is contiguous in the cited p66 body; hybrid joins spans with an ellipsis |
| AMD capex | Unsupported, p69 | Supported, p52 | Dense substitutes the 1,513 PP&E balance for 450 purchases; p52 explicitly states 2022 purchases of 450 million |
| AMD operating cash flow | Supported, p58 | Supported, p58 | 2022 operating cash flow 3,565 million |
| CVS revenue | Supported, p108 | Supported, p78 | 322,467 million; p78's consolidated-total column is valid alternative evidence |
| CVS attributable income | Unsupported, p108 | Supported, p108 | Dense takes 3.16 basic earnings per share and calls it millions; requested parent income is 4,149 million |
| CVS assets | False refusal | Indirect only, p110 | Hybrid matches 228,275 but quotes liabilities plus equity, not the assets row; not accepted as direct extractive support |
| CVS net PP&E | False refusal | Definition ambiguity, p119 | Note shows 13,117 including 244 of held-for-sale assets; fixed balance-sheet target is 12,873. See below. |
| CVS capex | False refusal | Unsupported, p151 | Hybrid quotes 185 million post-impairment asset fair value from the 2021 discussion, not 2022 capex of 2,727 |
| CVS operating cash flow | False refusal | Supported, p112 | Valid alternative reconciliation, 2022 operating cash flow 16,177 million |

Fixed numeric target matches: dense **5/12**, hybrid **9/12**. Original scoring is
unchanged; this is not equivalent to nine fully grounded answers. Strict direct
citation support: dense **5/7 delivered citations**; hybrid **8/11**, with one
unsupported and two indirect/definition-sensitive citations shown above. Target
match **and** direct citation support: dense **5/12**, hybrid **8/12**. Missing
citations on delivered factual answers: 0. Refusals: dense 5/12 and hybrid 1/12 on
answerable questions. No service/run errors occurred in either 15-question run.

The CVS PP&E question does not explicitly request the balance-sheet line. The note
amount is genuinely disclosed, and its footnote explains the 244-million
reclassification. This is an evaluation-definition ambiguity as well as an omitted
qualification in the delivered answer, not an invented number. Do not silently
change its gold label, call every mismatch a hallucination, or upgrade the headline
score after seeing outputs. A future dataset version should specify inclusion of
held-for-sale assets and obtain an independent annotation review.

Both methods correctly refused all three final probes: two deterministic scope
rejections (2030 year and IBM company) and one model refusal for undisclosed AMD
revenue from OpenAI. This is only one in-scope model-refusal probe per split. It does
not establish general resistance to unsupported questions.

## New Interactive Question

The browser submitted a question absent from both fixed manifests: "What were
3M's cash and cash equivalents at December 31, 2018, in USD millions?" The live
answer was 2,853 million, citing `3M_2018_10K:p60:row30` and the end-of-period cash
row. Original PDF 60 confirms the 2018 column. The
[live screenshot](images/live-cash-question.png) records the result, not a saved
replay. First-request wall time was 120.85 seconds including CPU index setup and
unloaded-model startup. The model-service loaded-model list was empty afterward.
