# AnchorReach Phase 6: Frozen Evaluation Protocol

## Frozen design

Protocol version `phase6_protocol_v1` was frozen on 2026-08-04 before collecting the holdout outputs or seeing any Phase-6 model scores.

- 12 public-source product slots × 5 markets = 60 holdout samples.
- Markets: US/en, DE/de, JP/ja, KR/ko, and AE/ar.
- Stable IDs use `AR-P01-US` through `AR-P12-AE`.
- The previous Wikimedia bottle result is calibration-only and excluded.
- Each sample uses the first completed generation only. Consistency-triggered regeneration is disabled for this evaluation.
- Two human raters score independently and cannot see model scores until both score sheets are locked.
- No paid call is authorized by this freeze. Public source URLs and licenses must be verified before generation.

The machine-readable source of truth is `docs/evaluation/phase6_evaluation_freeze.json`. Product categories, campaign-type allocation, logo-present/absent allocation, market allocation, weights, thresholds, and analysis rules cannot be changed after scores are observed. Any necessary change must create a new protocol version and retain this file.

## Why 60 samples

The design deliberately increases product diversity before adding more repetitions. Twelve product clusters cover varied silhouettes, materials, packages, and surface details. Five markets stress Latin, Japanese, Korean, and right-to-left Arabic layouts. Sixty rows support the overall correlation test, but the repeated market outputs for one product are not treated as fully independent evidence.

The primary claim is an overall judge-validation result across all 60 samples. Per-market results are secondary and descriptive because each market contains only 12 products. A claim that every market independently exceeds the correlation threshold would require at least 20 products per market and a separately frozen 100-sample design.

## Sample allocation

| Product slots | Campaign type | Logo condition | Samples |
| --- | --- | --- | ---: |
| P01–P04 | poster | present | 20 |
| P05–P08 | social_post | present | 20 |
| P09–P12 | ad_banner | absent | 20 |

Each product slot is crossed with all five markets. Every slot must be filled with a publicly accessible reference image whose reuse status is recorded. Logo-present slots require a separate reference mark with a recorded source and reuse status. Trademark restrictions must be noted even when copyright permits local evaluation.

## Collection order and leakage controls

1. Select and record all 12 public product sources and the eight logo sources.
2. Verify every URL, image decode, license note, and product category before any paid generation. This was completed on 2026-08-04 and is recorded in `docs/evaluation/phase6_public_sources.json` and `docs/PHASE6_PUBLIC_SOURCE_AUDIT.md`.
3. Generate all 60 assets in stable sample-ID order. Retain the first completed output; do not select the best-looking attempt.
4. Randomize the display order separately for each human rater while preserving hidden sample IDs.
5. Each rater compares the same ordered references and generated asset used by the model judge.
6. Lock both human score sheets before running or importing model scores.
7. Preserve provider failures as operational failures. They are not scores and cannot be silently dropped; a replacement policy must be documented before rerunning.

## Human scoring

Both raters score each active dimension from 0 to 100 using the following anchors. Intermediate values are allowed.

| Score anchor | Meaning |
| ---: | --- |
| 100 | No visible inconsistency in the locked dimension. |
| 80 | Minor visible deviation that preserves identity and essential appearance. |
| 60 | Material inconsistency; lowest acceptable boundary. |
| 40 | Major inconsistency that changes a defining property. |
| 20 | Very weak match with only limited recognizable evidence. |
| 0 | Missing, unrelated, or opposite to the locked reference. |

Logo-present samples use the frozen `logo_hard_gate_v2` policy. Core-color change, defining-structure change, wording change, missing reference mark, or invented alternate mark caps that rater's logo policy score at 59 while retaining the raw score and reason. Logo-absent samples leave the logo field blank; product and color weights are normalized.

The two policy-adjusted human dimension scores are averaged after both sheets are locked. No discussion or adjudication may use model scores. Inter-rater Pearson, Spearman, and mean absolute difference must be reported alongside the human-vs-model result.

## Model scoring and statistical claims

The model judge uses the same frozen scoring policy and ordered image inputs. The primary trust gate remains:

- sample count is at least 20;
- overall-score Pearson correlation is strictly greater than 0.8; and
- overall-score Spearman correlation is strictly greater than 0.8.

The report must also include a 95% product-cluster bootstrap interval so the five repeated markets for a product are not misrepresented as five independent products. Market-level values, pass rates, hard-gate counts, provider failures, latency, token usage, and actual cost are reported without changing the primary threshold.

If the trust gate fails, the result remains a valid project finding. Samples, thresholds, weights, and exclusions cannot be changed to improve the number after inspection.

## Financial gate

Based on the completed baseline, one generation plus one independent judge call is estimated at USD 0.097741 per sample. The 60-sample base estimate is USD 5.86446. A later execution cap of USD 6.50–7.00 is recommended to cover limited provider failures, but **no paid execution is authorized** by this document. The environment must remain at a zero-dollar judge allowance until the user explicitly approves a new amount.

## Phase-6 completion checklist

- [x] Freeze protocol, markets, product slots, sample IDs, raters, and analysis rules.
- [x] Select 12 public product sources and eight eligible logo sources.
- [x] Verify all source URLs, decode behavior, reuse status, and trademark notes.
- [ ] Obtain explicit generation and judge budget approval.
- [ ] Generate and archive 60 first-attempt assets.
- [ ] Complete and lock two independent human score sheets.
- [ ] Run the independent model judge on the frozen outputs.
- [ ] Calculate inter-rater, overall judge, clustered uncertainty, and secondary market metrics.
- [ ] Publish the reproducible Phase-6 report with actual costs and limitations.
