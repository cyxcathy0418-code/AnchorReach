# AnchorReach Phase 4: Market Localization Layer

Phase 4 adds deterministic market briefs between the validated structured input and the existing Open-AI-Design-Agent planning loop. It does not replace the upstream agent or use Creative Lab code or data.

## Outcome

- Five curated presets are available: United States, Germany, Japan, South Korea, and the United Arab Emirates.
- A single campaign still accepts one to three unique target markets.
- Each market receives explicit language, locale, copy, typography, layout-direction, adaptation, and publication-review instructions.
- Arabic output uses a right-to-left layout while product images and logos are never mirrored.
- Unknown API markets receive a visible generic fallback and warning rather than invented local rules.
- The Agent prompt requires one separately labelled static asset per market.
- Prices, discounts, tests, certifications, endorsements, availability, guarantees, and health claims may not be invented.
- Compliance items are human review prompts, not automated legal clearance.
- No MuAPI or OpenAI request was made during Phase-4 implementation; implementation cost was USD 0.

## Data flow

```text
StructuredCampaignInput
  -> deterministic AnchorBlock
  -> versioned LocalizationPlan
  -> Agent prompt with campaign + anchors + market briefs
  -> existing Open-AI-Design-Agent plan / approval / generation loop
  -> existing post-generation consistency workflow
```

The `POST /api/v1/anchor-reach/structured-input` response now includes `localization_plan`. The plan is also stored with the visible user message so a saved session retains the brief used for generation.

## Curated presets

| Market | Default locale | Direction | Creative emphasis | Publication-review emphasis |
| --- | --- | --- | --- | --- |
| United States | `en-US` | LTR | concise benefit-first hierarchy | claim substantiation, clear disclosures, endorsements |
| Germany | `de-DE` | LTR | precise German and space for longer copy | accurate offer information, total price, prior-price review |
| Japan | `ja-JP` | LTR | natural Japanese, polite tone, controlled line breaks | misleading superiority/price claims and sponsored content |
| South Korea | `ko-KR` | LTR | natural Korean and Hangul-aware spacing | false, exaggerated, deceptive, or unfair comparison claims |
| United Arab Emirates | `ar-AE` | RTL | natural Arabic and mirrored text hierarchy | clear labels, declared price, false data, regulated-category review |

The UAE preset also accepts English and switches the computed locale and direction to `en-AE` / LTR.

## Regulatory-source boundary

The prompts were reviewed on 2026-08-04 against public regulator or government guidance:

- United States: [FTC Advertising and Marketing](https://www.ftc.gov/business-guidance/advertising-marketing) and [Advertising FAQs](https://www.ftc.gov/business-guidance/resources/advertising-faqs-guide-small-business).
- Germany / EU: [EU unfair commercial practices](https://europa.eu/youreurope/citizens/consumers/unfair-treatment/unfair-commercial-practices/index_en.htm) and [EU unfair pricing](https://europa.eu/youreurope/citizens/consumers/unfair-treatment/unfair-pricing/index_en.htm).
- Japan: [Consumer Affairs Agency — Establishing Trusted Representation](https://www.caa.go.jp/en/policy/representation/).
- South Korea: [Korea Fair Trade Commission — Regulation on Unfair Labeling and Advertising](https://www.ftc.go.kr/eng/contents.do?key=557) and [laws and guidelines](https://www.ftc.go.kr/eng/selectBbsNttList.do?bordCd=847&key=577).
- United Arab Emirates: [Official UAE Government — Consumer protection](https://u.ae/en/information-and-services/justice-safety-and-the-law/consumer-protection).

These sources inform a small preflight checklist only. They do not cover every category, emirate/state, platform, promotion, or later rule change. A qualified human must review the final asset and current requirements before publication.

## Code locations

| Responsibility | Location |
| --- | --- |
| Localization response contracts | `server/app/schemas/structured_input.py` |
| Versioned market presets | `server/app/services/market_localization.py` |
| Agent-prompt integration | `server/app/services/prompt_builder.py` |
| API assembly and fallback warnings | `server/app/routers/anchor_reach_router.py` |
| Nontechnical market selector | `packages/design-agent/src/components/StructuredCampaignForm.jsx` |
| Brief persistence and review table | `packages/design-agent/src/CreativeCanvas.jsx` |
| Automated Phase-4 tests | `server/tests/test_market_localization.py` |

## Verification

- Backend suite: 38 passed, 0 failed.
- Five curated presets: covered.
- UAE Arabic RTL and English LTR behavior: covered.
- Three-market order and separate-asset instruction: covered.
- Unknown-market fallback warning: covered.
- Duplicate-market rejection: covered.
- Human-review disclaimer and no-invented-claims rule: covered.
- Design Agent component build: passed.
- Full Next.js production build: passed.

No paid multi-market generation was run. Phase 4 is locally implementation-complete; visual quality across markets remains part of the deferred paid evaluation layer.
