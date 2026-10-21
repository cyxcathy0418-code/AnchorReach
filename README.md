# AnchorReach

> A cross-border e-commerce creative Agent built on Open-AI-Design-Agent: structured product briefs, deterministic visual anchors, market localization, explainable post-generation consistency checks, and capped correction loops.

[Current project status](docs/PROJECT_STATUS.md) · [PRD](docs/PRD_ANCHORREACH.md)

## Product

AnchorReach is designed for small cross-border e-commerce teams that need static campaign assets for several markets without maintaining a local creative team in each market. A user supplies product references, selling points, brand information, one to three target markets, and a campaign type. The system then:

1. validates the campaign and source images;
2. creates an auditable `AnchorBlock` for product appearance, Logo, and color;
3. adds a versioned localization brief for each market;
4. hands the structured prompt to the original Agent plan / route / execute / assemble loop;
5. compares generated assets with the locked anchors using an independent vision judge;
6. explains discrepancies and allows at most two corrective generations.

The current presets cover the United States, Germany, Japan, South Korea, and the UAE. One campaign remains limited to three markets. Arabic uses RTL composition without mirroring product images or Logos.

## Architecture

```text
Product brief
  -> strict schema and image validation
  -> deterministic AnchorBlock
  -> per-market LocalizationPlan
  -> upstream Design Agent planning and generation (MuAPI)
  -> independent consistency report (OpenAI vision judge)
  -> pass or capped corrective generation
  -> auditable asset and report history
```

## Delta from the upstream project

| Area | Upstream Open-AI-Design-Agent | AnchorReach |
| --- | --- | --- |
| Input | Free-form creative chat | Strict product / market / campaign schema |
| Brand constraints | Reference conditioning in the generation flow | Explicit locked `AnchorBlock` |
| Localization | Market can be mentioned in free text | Versioned copy, layout, locale, RTL, and review briefs |
| Validation | No published post-generation consistency judge | Explainable independent judge and hard Logo gate |
| Correction | User-led editing and regeneration | Maximum three total attempts with budget gates |
| Evaluation | Demo outputs, no formal public rater study | Frozen 60-sample protocol; paid collection intentionally deferred |
| Cost control | Visible upstream plan credits | Explicit per-call judge authorization and reproducible unit economics |

## Verified evidence

- 42 backend tests pass; the Design Agent component and full Next.js production build pass.
- One real MuAPI generation loop and one independent OpenAI judge call completed.
- The real generation spent USD 0.18 across two charged attempts; the valid independent judge call was estimated at USD 0.007741.
- The calibration judge returned 93.4 but disagreed with manual strict-Logo interpretation. The raw result is preserved, the Logo hard gate was tightened, and judge trust is **not** claimed.
- Twelve public product sources and eight Logo sources were license-checked for the frozen evaluation design.
- A 60-sample, five-market, two-human-rater protocol is frozen, but generation, ratings, and correlation results have not been collected.
- Phase-4 and Phase-5 implementation work made no paid model calls.

See [Phase 2](docs/PHASE2_STRUCTURED_INPUT.md), [Phase 3](docs/PHASE3_CONSISTENCY_VALIDATION.md), [Phase 4](docs/PHASE4_MARKET_LOCALIZATION.md), [Phase 5](docs/PHASE5_COMMERCIALIZATION_DESIGN.md), and [Phase 6](docs/PHASE6_EVALUATION_PROTOCOL.md).

## Run locally

Backend:

```bash
cd server
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Frontend, from the repository root:

```bash
npm install
npm run dev:app
```

Tests:

```bash
./.venv/bin/pytest server/tests -q
```

Paid judge calls are disabled by default. Never commit `server/.env`; use the checked-in `.env.example` only.

## Honest scope

- Static images only; video and digital-human output are outside the AnchorReach MVP.
- The AnchorBlock extractor records deterministic image metadata and colors; it does not claim semantic vision recognition of shape, material, or Logo text.
- Localization compliance items are publication-review prompts, not legal clearance.
- Judge trust, multi-market output quality, willingness to pay, revenue, conversion, and retention remain unvalidated.
- The hosted pricing packages are cost-derived hypotheses, not current products or revenue.

## Repository map

| Area | Location |
| --- | --- |
| AnchorReach API | `server/app/routers/anchor_reach_router.py` |
| Structured contracts | `server/app/schemas/structured_input.py` |
| Anchor extraction | `server/app/services/anchor_extractor.py` |
| Market presets | `server/app/services/market_localization.py` |
| Consistency service | `server/app/services/consistency_service.py` |
| Independent judge | `server/app/services/openai_vision_judge.py` |
| Structured UI | `packages/design-agent/src/components/StructuredCampaignForm.jsx` |
| Evaluation artifacts | `docs/evaluation/` and `outputs/` |

