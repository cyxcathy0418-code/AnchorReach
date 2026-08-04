# AnchorReach Product Requirements Document

Version: `v1.1-implemented-scope`
Updated: 2026-08-04

## Positioning

AnchorReach is an AI creative Agent for small cross-border e-commerce teams. A team provides product and brand references once, selects one to three target markets, and receives separately localized static campaign assets that can be checked against locked visual anchors.

The project is a portfolio-oriented second development of `Anil-matcha/Open-AI-Design-Agent`. It demonstrates Agent orchestration, structured product design, AIGC generation, evaluation discipline, and cost controls. It is not presented as an operating SaaS business.

## Target user

- A 5–30-person cross-border e-commerce team.
- Operates an independent store and one or more third-party channels.
- Does not maintain a dedicated creative team for every target market.
- Needs repeatable static posters, social posts, and advertising banners.

## Core problem

Free-form generation can create visually attractive outputs while changing product geometry, a Logo, or a brand color. Repeating one source asset across languages also does not create a credible localized campaign. Users need both explicit invariants and market-specific generation instructions, with visible evidence when an output fails.

## Product flow

```text
Structured product input
  -> source validation
  -> AnchorBlock extraction
  -> market localization briefs
  -> Agent planning and generation
  -> consistency scoring and explanation
  -> pass or capped correction
  -> asset and audit output
```

## Functional requirements

### Structured input

- Product category, selling points, image references, brand name, optional Logo, and optional primary color.
- One to three unique target markets.
- Campaign type: poster, social post, or advertising banner.
- Missing required fields and unreadable images block generation with field-level errors.

### AnchorBlock

- Product appearance instruction derived from verified reference metadata.
- Optional Logo reference.
- Brand color palette from an explicit color or deterministic image extraction.
- `locked_attributes` is the only source of truth for dimensions that the judge evaluates.

### Agent generation

- Reuse the upstream plan, route, execute, assemble, approval, and asset-history flow.
- Generate static assets only for the AnchorReach MVP.
- Create a separate labelled asset for each market.

### Consistency loop

- Compare generated assets only against active locked dimensions.
- Return 0–100 dimension scores, visible evidence, discrepancies, and a weighted overall score.
- A strict Logo hard gate covers changed core color, changed mark structure, changed wording, missing marks, and invented marks.
- Permit at most three total generation attempts.
- Provider errors stop explicitly and never become fabricated scores.

### Market localization

- Curated presets: US/en, DE/de, JP/ja, KR/ko, and AE/ar or en.
- One campaign selects at most three markets.
- Each preset defines locale, text direction, copy guidance, visual guidance, required adaptations, and publication-review prompts.
- Never invent prices, discounts, test results, certifications, endorsements, availability, guarantees, or health claims.
- Compliance prompts do not constitute legal clearance.

### Commercial design

- Self-hosted open-source mode remains free; operators pay their own providers.
- Hosted packages are a future cost-derived hypothesis.
- A future hosted service must show and reserve the maximum provider budget before plan approval and settle from provider-reported cost.
- No payment integration is required for this portfolio MVP.

## Nonfunctional requirements

- Preserve upstream framework attribution and MIT license.
- Do not use Creative Lab code or data.
- Keep secrets out of source control.
- Disable paid judge calls without an explicit local budget.
- Preserve raw reports, policy versions, usage, cost, and source digests for audit.
- All public metrics must be reproducible from repository evidence.

## Success criteria

Implemented criteria:

- Structured input and field-level errors work locally.
- One real end-to-end generation and judge loop has run.
- Explainable consistency results and correction limits are implemented.
- Five localization presets are implemented, with no more than three selected per campaign.
- Tests and production builds pass.

Deferred evidence criteria:

- At least 20 blind human/model score pairs.
- Pearson and Spearman correlations both greater than 0.8 before the judge may be called trusted.
- Full 60-sample, two-rater evaluation report.
- Real multi-market output-quality assessment.

Failure to meet a deferred threshold must be reported as a result, not hidden or tuned away.

## Scope exclusions

- Video and digital-human generation.
- Semantic visual recognition in the deterministic extractor.
- Automated legal approval.
- Production billing, Stripe, and real subscription entitlements.
- Claims of revenue, conversion, retention, customer count, or validated willingness to pay.

## Delivery status

| Stage | Deliverable | Status |
| --- | --- | --- |
| 0 | Positioning and AnchorReach name | Complete |
| 1 | Environment and real baseline call | Complete |
| 2 | Structured input and AnchorBlock | Complete |
| 3 | Consistency judge and correction loop | Implementation complete; trust unvalidated |
| 4 | Market localization | Locally complete; paid visual validation deferred |
| 5 | Commercial design | Complete as a hypothesis; billing not implemented |
| 6 | Evaluation | Protocol and sources complete; paid collection deferred |
| 7 | Portfolio and publication package | Complete locally; GitHub publication tracked separately |
