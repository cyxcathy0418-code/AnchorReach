# AnchorReach Phase 2: Structured Input Layer

This phase adds a strict, local input layer in front of the existing Open-AI-Design-Agent workflow. The upstream MuAPI agent loop remains responsible for planning, routing, execution, and assembly.

## Source boundary

- Framework and integration baseline: `Open-AI-Design-Agent`.
- Creative Lab code, data, fixtures, and generated outputs used: **none**.
- The anchor extractor in this repository is an original, deterministic implementation.

## Pre-implementation findings

The original client accepted free text in `packages/design-agent/src/CreativeCanvas.jsx`. `sendMessage` submitted that text to `/api/v1/creative-agent/sessions/{session_id}/chat`. The FastAPI route in `server/app/routers/creative_agent_router.py` forwarded the JSON body to MuAPI without a local product schema or anchor extraction step.

Phase 2 introduces `POST /api/v1/anchor-reach/structured-input`. The client validates a structured campaign through this endpoint, persists the returned `structured_input` and `anchor_block` in the local message record, and passes the generated adapter prompt into the existing agent chat flow.

## Code locations

| Responsibility | Location |
| --- | --- |
| Input and AnchorBlock schemas | `server/app/schemas/structured_input.py` |
| Image loading and anchor extraction | `server/app/services/anchor_extractor.py` |
| Base-agent prompt adapter | `server/app/services/prompt_builder.py` |
| Local API route and language warnings | `server/app/routers/anchor_reach_router.py` |
| Structured campaign form | `packages/design-agent/src/components/StructuredCampaignForm.jsx` |
| Client integration | `packages/design-agent/src/CreativeCanvas.jsx` |
| Unit/API tests | `server/tests/test_structured_input.py` |
| Reproducible acceptance output | `docs/stage2_acceptance_evidence.json` |

## Validation behavior

- `product.category`, `core_selling_points`, `images`, and `brand_name` are required.
- Product images and an optional logo must be reachable/readable, below 15 MB, and decodable as real images.
- `target_markets` accepts 1–3 entries. Market codes remain open and extensible through two-letter format validation rather than a closed enum.
- Unusual market/language combinations produce warnings and do not block the request.
- `campaign_type` accepts only `poster`, `social_post`, or `ad_banner`.
- Missing `logo_url` is explicit (`logo_reference: null`) and is not included in `locked_attributes`.
- Missing `primary_color` triggers deterministic palette extraction from visible image pixels.
- Every blocking failure returns a field path and reason; no empty/default AnchorBlock is returned.

## Extraction method and limitation

The local extractor decodes every image and records dimensions, format, color mode, transparency, and dominant colors. `product_appearance` instructs downstream models to preserve the exact silhouette, proportions, surface details, packaging geometry, and visible brand markings from those verified references.

It does **not** claim semantic vision-model recognition of shapes, materials, or logo text. Adding a paid or locally hosted vision model would be a separate, explicit enhancement. This limitation is kept visible to avoid contaminating later consistency-evaluation numbers.

## Run and verify

From `server/`:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python scripts/generate_stage2_evidence.py
uvicorn app.main:app --reload --port 8000
```

From the repository root, use the base project's normal client commands:

```bash
npm run install:all
npm run build:lib
npm run dev:app
```

Open `http://localhost:3000/canvas`. The Structured brief mode is selected by default; Free text remains available for backward compatibility.

The local schema and anchor endpoint does not require a MuAPI key. Continuing from a validated brief into actual asset generation still requires `MU_API_KEY` in `server/.env`, matching the base project.
