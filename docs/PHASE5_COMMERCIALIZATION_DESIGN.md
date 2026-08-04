# AnchorReach Phase 5: Commercialization Design

Phase 5 defines a reproducible commercialization hypothesis for a future managed AnchorReach service. It does not add payments, sell a subscription, or claim demand validation.

## Decision

Use two clearly separated distribution modes:

1. **Self-hosted open source:** the MIT code remains free. The operator supplies and pays for their own MuAPI and OpenAI usage.
2. **Future managed service:** AnchorReach hosts the workflow, budget controls, localization presets, consistency reports, history, and support. The proposed packages below apply only to this hosted version.

The primary motion is product-led SaaS with optional prepaid usage packs. White-label or partner distribution remains a later sales path and should use a minimum commitment plus metered provider usage, not an invented public price before partner discovery.

## Evidence used

The only real closed-loop sample produced this initial cost evidence:

| Cost item | Observed / estimated cost |
| --- | ---: |
| One MuAPI image-generation request | USD 0.090000 |
| One OpenAI independent judge request | USD 0.007741 |
| First-pass verified asset | USD 0.097741 |
| One corrected asset, two complete attempts | USD 0.195482 |
| Maximum three-attempt verified asset | USD 0.293223 |
| Three-market campaign, first pass | USD 0.293223 |
| Three-market campaign, all three attempts | USD 0.879669 |

The sample contained one provider timeout that still reduced the MuAPI balance by USD 0.09. The model therefore does not assume every failed request is free. This is conservative and follows the observed ledger rather than a marketing claim.

The MuAPI documentation describes prepaid credits, per-generation deduction, per-request USD/credit cost metadata, refund status, and account-balance headers. These fields should drive future settlement rather than an invented fixed conversion between MuAPI credits and dollars: [MuAPI Credits](https://muapi.ai/docs/credits). The current judge uses GPT-5.4 mini at USD 0.75 per million input tokens and USD 4.50 per million output tokens, matching OpenAI's published rates reviewed on 2026-08-04: [OpenAI GPT-5.4 mini](https://openai.com/index/introducing-gpt-5-4-mini-and-nano/).

The evidence is one calibration case. It supports a transparent first model, not a stable average cost forecast.

## Anchor Credit policy

For the hypothetical hosted service, define **1 Anchor Credit as USD 0.01 of reserved AI-provider budget**. It is an internal budget unit and is not claimed to equal one MuAPI credit.

| Action | Initial budget charge |
| --- | ---: |
| One observed USD 0.09 generation | 9 Anchor Credits |
| One observed USD 0.007741 judge call | 1 Anchor Credit |
| First-pass verified asset | 10 Anchor Credits |
| Verified asset with the full three-attempt cap | 30 Anchor Credits |
| Three-market first-pass campaign | 30 Anchor Credits |
| Three-market campaign with the full retry cap | 90 Anchor Credits |

Rules:

- Calculate each provider action from its current catalog estimate and round up to the next Anchor Credit.
- Show and reserve the maximum before the user approves the Agent plan.
- Settle from provider-reported actual cost after completion.
- Restore credits only when the provider reports a refund or zero charge.
- Never start a retry that would exceed the campaign or account balance.
- Recheck supplier pricing before enabling any paid model or changing the underlying model.

This reuses the base project's visible plan/approval interaction and cost events while protecting against runaway Agent spending.

## Package hypothesis

| Package | Proposed price | Included allowance | Scope | Status |
| --- | ---: | ---: | --- | --- |
| Sandbox | USD 0 | 20 one-time credits | One market, draft generation only, no judge or auto-correction | Launch hypothesis |
| Pro | USD 29/month | 1,200 credits | Five available presets, up to three markets per campaign, judge and capped correction | Primary launch hypothesis |
| Team | USD 79/month | 3,600 credits | Pro plus future shared workspace, approval roles, and team usage | Post-MVP; do not sell yet |
| Credit Pack | USD 9.90 once | 350 credits | Additional metered use | Launch hypothesis |

The free allowance is one-time rather than five free generations every month. At the observed cost, an unlimited recurring free allocation creates avoidable abuse exposure before activation and conversion are known.

### Variable-cost margin ceiling

If every included credit is consumed, the maximum AI-provider reserve and remaining revenue are:

| Package | Revenue | AI reserve | Revenue less AI reserve | Variable-cost gross margin |
| --- | ---: | ---: | ---: | ---: |
| Pro | USD 29.00 | USD 12.00 | USD 17.00 | 58.62% |
| Team | USD 79.00 | USD 36.00 | USD 43.00 | 54.43% |
| Credit Pack | USD 9.90 | USD 3.50 | USD 6.40 | 64.65% |

These are **not** contribution margins or operating profits. They exclude payment processing, hosting, storage, monitoring, support, taxes, refunds, acquisition, fraud, and supplier-price changes.

## Packaging rationale

- **Sandbox** proves time-to-first-draft at a maximum provider exposure of USD 0.20 per activated account.
- **Pro** is the main product for the stated 5–30-person cross-border e-commerce team. At full usage, it preserves USD 17 before non-provider costs.
- **Team** is only a pricing placeholder. Selling it before collaboration features exist would misrepresent the product.
- **Credit Pack** accommodates campaign spikes without forcing a recurring-plan change.
- Expensive model selection consumes more credits rather than silently eroding margin.
- Consistency correction is not advertised as “free retries”; each provider action remains visible and budgeted.

## Go-to-market sequence

1. Use the free self-hosted repository as technical proof and developer acquisition.
2. Offer the one-time hosted Sandbox for nontechnical users.
3. Validate whether users reach a first usable localized draft and understand the consistency report.
4. Test the USD 29 Pro hypothesis only after measuring activation and provider cost across real sessions.
5. Add Team only after shared workspace, approvals, and usage reporting are implemented.
6. Explore white-label distribution only after partner interviews establish integration scope and support load.

No claim should be made that these users, prices, conversions, or revenues already exist.

## Metrics

Primary product metric:

- Monthly count of assets that pass consistency review and are accepted by the user.

Activation and quality:

- Time to first generated localized asset.
- Structured-brief completion rate.
- Plan approval rate.
- First-attempt consistency pass rate.
- User acceptance after pass and after correction.

Cost and reliability guardrails:

- Provider cost per accepted asset and per three-market campaign.
- Mean paid attempts per accepted asset.
- Charged provider failure rate.
- Judge cost and latency.
- Credits reserved versus settled.
- Variable AI cost as a percentage of hosted revenue.

Commercial metrics, only after a real hosted launch:

- Sandbox activation and Pro conversion.
- Credit utilization and pack attach rate.
- Monthly retention and downgrade/cancellation.
- Support cost per active account.

## Claim boundary

Allowed portfolio statement:

> Built a cost-derived monetization model from audited provider usage, with plan-level spend approval, per-action credit settlement, and a USD 29/month hosted-service hypothesis.

Not allowed before real market evidence:

- “Users are willing to pay USD 29.”
- “The product has a 58.62% gross margin.”
- “The free tier converts to paid.”
- Any revenue, retention, CAC, LTV, or customer-count claim.

The precise machine-readable assumptions and calculations are stored in `docs/commercial/phase5_unit_economics.json`.
