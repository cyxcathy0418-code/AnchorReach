# AnchorReach Phase 3: Explainable Consistency Validation

Phase 3 inserts a real post-generation judge between the existing Open-AI-Design-Agent generation loop and final delivery. It scores only the dimensions listed in the Phase-2 `AnchorBlock.locked_attributes`, explains visible evidence and discrepancies, and can request at most two corrective generations after the original attempt.

## Source boundary

- Framework, session flow, asset events, planning, approval, and generation remain based on `Open-AI-Design-Agent`.
- Planning, routing, reference handling, and generation continue to use MuAPI exactly as the base project does.
- Consistency scoring uses an independent OpenAI Responses API vision model so generation and acceptance are not judged through the same provider path.
- Creative Lab code, data, fixtures, and outputs used: **none**.

## Runtime flow

1. The existing agent returns one or more generated static-image assets.
2. The client submits each image, its `AnchorBlock`, and its attempt number to `POST /api/v1/anchor-reach/consistency-check`.
3. The judge compares up to four ordered images: product references, optional logo reference, and the generated asset.
4. The server validates the judge's strict JSON response and calculates the weighted score itself.
5. The UI shows the overall score, every dimension score, visible evidence, and concrete discrepancies.
6. A failed result generates a correction prompt containing the failed dimensions and original immutable `AnchorBlock`.
7. The existing agent loop performs the correction. The cycle stops after a pass or three total attempts.

Provider failures, missing keys, timeouts, malformed judge responses, and missing generated images stop the loop explicitly. They never become a fabricated score and never trigger an ungrounded retry.

## Scoring policy v2 (frozen before the validation set)

The first paid public sample is a calibration sample, not part of the final blind validation set. Policy v1 exposed a rubric defect: the judge gave the locked logo 96 while acknowledging that its exact color treatment changed. Policy v2 below was therefore frozen before collecting the 20-sample evaluation set; the v1 result remains preserved and is not retroactively rewritten.

| Dimension | Base weight |
| --- | ---: |
| Product appearance | 50% |
| Logo reference | 30% |
| Color palette | 20% |

Only locked dimensions are active. If the logo is absent, the remaining weights are normalized to product appearance 71.4286% and color palette 28.5714%. The calculation is:

`overall = sum(dimension_score × normalized_weight)`

A result passes only when both conditions hold:

- overall score is at least 80;
- every active locked dimension is at least 60.

When `logo_reference` is locked, the logo is an exact identity constraint rather than a recognizability target. Any of the following triggers a hard failure:

- a core logo color changes, including a multicolor mark rendered as monochrome;
- the mark's defining structure changes;
- brand wording is added, removed, or altered;
- the reference mark is missing;
- an invented or alternate brand mark appears.

Minor antialiasing, proportional scaling, and compression artifacts alone do not trigger the hard gate. When a severe violation is reported, the server preserves the raw judge score for audit, caps the policy score at 59, and forces the logo dimension to fail even if a caller configures a lower minimum score.

These values are sent in the API request and can be changed explicitly; the client currently predeclares 80/60 before any evaluation data is observed. The retry cap is three total attempts (original plus two corrections).

## Judge contract and audit data

The judge must return, for every active dimension:

- a 0–100 score;
- one or more visible evidence statements;
- zero or more concrete discrepancies.
- logo hard-failure codes and visible reasons; non-logo dimensions must return empty hard-failure arrays.

Every report also records the scoring-policy version, raw and policy-adjusted dimension scores, hard-gate status, provider, model, UTC timestamp, latency, ordered image URLs, generated-asset URL, input/output token usage, estimated API cost, configured per-call limit, and a SHA-256 digest of the raw model response. The digest makes it possible to detect later report/source mismatches without storing unbounded hidden reasoning.

The OpenAI judge is disabled financially by default: `ANCHORREACH_JUDGE_MAX_COST_USD=0` stops before any request. The current implementation accepts an explicitly approved limit no higher than USD 0.02 per call and performs a conservative token preflight before contacting the provider.

## Judge trustworthiness protocol

PRD acceptance requires both Pearson and Spearman correlation between human and model scores to be greater than 0.8. The implementation does not claim that result before real ratings exist.

The predeclared pilot protocol is:

1. Freeze at least 20 generated samples and assign stable `sample_id` values.
2. Have a human evaluator score product appearance, optional logo, and color palette from 0–100 without seeing model scores.
3. Export judge dimension scores separately, using the same sample IDs.
4. Calculate both overall scores with the same 50/30/20 weighting and absent-logo normalization.
5. Run the correlation tool. The judge is marked trusted only if sample count is at least 20 and **both** correlations are strictly greater than 0.8.
6. If either value misses the threshold, retain and report the result; do not tune the threshold or remove inconvenient samples after seeing the outcome.

Blank templates are under `docs/evaluation/`. Run:

```bash
cd server
python scripts/validate_judge_correlation.py \
  --human ../docs/evaluation/human_scores.csv \
  --model ../docs/evaluation/model_scores.csv \
  --output ../docs/evaluation/judge_correlation_result.json
```

## Code locations

| Responsibility | Location |
| --- | --- |
| Request/report contracts | `server/app/schemas/consistency.py` |
| Independent OpenAI multi-image judge and cost guard | `server/app/services/openai_vision_judge.py` |
| Legacy MuAPI judge retained for fallback comparison | `server/app/services/vision_judge.py` |
| Weights, pass policy, correction prompt | `server/app/services/consistency_service.py` |
| Consistency API | `server/app/routers/consistency_router.py` |
| Human/model correlation logic | `server/app/services/judge_validation.py` |
| Correlation command | `server/scripts/validate_judge_correlation.py` |
| UI loop and report card | `packages/design-agent/src/CreativeCanvas.jsx` |
| Automated tests | `server/tests/test_consistency.py`, `server/tests/test_judge_validation.py` |

## Configuration and verification

Copy `server/.env.example` to `server/.env`, then set `MU_API_KEY` for generation and `OPENAI_API_KEY` for independent scoring. Do not commit the `.env` file. Leave `ANCHORREACH_JUDGE_MAX_COST_USD=0` until a paid call has been explicitly approved.

```bash
cd server
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

```bash
cd packages/design-agent
npm run build
```

The current evidence status is recorded in `docs/stage3_acceptance_status.json`. Automated policy/API tests, the component build, one real MuAPI generation, and one independent OpenAI judge call are complete. Judge trust and human/model correlation remain deliberately unclaimed: the first valid report passed the logo dimension while also noting that its exact locked color treatment changed.

## Selected public acceptance sample

The fixed sample is `docs/evaluation/public_sample_campaign.json`: a blue Wikimedia bottle illustration for an English Singapore social post. The product image is CC0; the separate logo file has public-domain copyright status but remains subject to Wikimedia trademark rules, so this sample is for local technical validation only.

Both image URLs were checked for HTTP 200 responses. The real Phase-2 endpoint then downloaded and decoded both files successfully, returned all three locked attributes, fixed the supplied blue anchor to `#1688D4`, and returned no warnings.

The public sample produced one real MuAPI asset and one independent OpenAI judge report:

1. The judge returned a valid strict report in one call with an overall score of 93.4.
2. Usage was 6,745 input tokens and 596 output tokens; estimated cost was USD 0.007741 under the approved USD 0.02 ceiling.
3. The automated logo score was 96 even though the report acknowledged that the exact locked logo color treatment was not preserved.
4. Record this as a real rubric disagreement, not as proof that the judge is trustworthy.
5. Policy v2 now freezes the strict-logo hard gate; the next evaluation must use new holdout samples rather than rescoring this calibration case as if it were unseen.

This single case proves the real technical loop. It does not prove judge trustworthiness; that separate claim requires at least 20 paired blind human/model samples under the predeclared correlation protocol above.
