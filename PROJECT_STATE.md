# Project State — E-Commerce Growth Analytics

*Living handoff document. Update this file at the end of every working session.*
*Last updated: 2026-06-05 (margin mix scenario analysis complete)*

---

## Current Phase

**Margin Mix Scenario Analysis — complete. Next: PROJECT_PROGRESS.md and A/B test recommendations.**

Growth lever scorecard completed across five lever types. Cart-to-purchase conversion is the highest-upside lever; margin mix shift has much smaller upside than expected.

---

## Project Goal

Build a polished, end-to-end analytics portfolio project targeting Data Analyst, Product Analyst, BI Analyst, and startup analytics roles. Analyze the theLook eCommerce dataset to identify where an e-commerce business is leaking growth.

---

## Core Business Question

> "Where is this e-commerce business leaking growth: acquisition, conversion, retention, product mix, or fulfillment?"

---

## Starting Hypothesis

> "The business is likely losing more growth through conversion quality, repeat purchasing, and post-purchase experience than through raw acquisition volume alone."

The final narrative will follow the data — this hypothesis is a directional starting point only.

---

## Dataset

- **Name:** theLook eCommerce
- **Location:** `bigquery-public-data.thelook_ecommerce` (Google BigQuery public dataset)
- **Key tables:** `orders`, `order_items`, `users`, `products`, `inventory_items`, `events`, `distribution_centers`

---

## Access Method Status

- [x] BigQuery console access confirmed
- [x] Google Cloud CLI and bq CLI configured and tested (project: gen-lang-client-0200890233)
- [ ] Python `google-cloud-bigquery` connection tested
- [ ] Service account / credentials configured

*Note: Project is transitioning to a local raw data workflow (see Current Workflow). BigQuery remains the authoritative source dataset; raw tables will be downloaded once into `data/raw/` and queried locally via Python/DuckDB for all future analysis.*

---

## Key Decisions Made

- Project scope set to 5 growth leakage themes: acquisition, conversion, retention, product, fulfillment
- Starting hypothesis established as guide, not conclusion
- Tool split defined: ChatGPT for framing, Claude Code for implementation
- No predictive modeling in scope

---

## Completed Work

- [x] Project folder structure created
- [x] PROJECT_PLAN.md written
- [x] PROJECT_STATE.md created
- [x] CLAUDE.md created
- [x] IDEAS_BACKLOG.md created
- [x] README.md created
- [x] .gitignore created
- [x] requirements.txt created
- [x] Confirmed BigQuery sandbox access by successfully querying bigquery-public-data.thelook_ecommerce.orders and returning 125,408 orders.
- [x] Configured Google Cloud CLI for project gen-lang-client-0200890233.
- [x] Confirmed bq CLI access by querying bigquery-public-data.thelook_ecommerce.orders from terminal and returning 125,408 orders.

---

## Phase 6 — Margin Mix Scenario Analysis (Complete)

- [x] `src/build_margin_mix_scenarios.py` created and committed — DuckDB + Python hybrid; reads data/processed/ and prior analysis CSVs; computes margin mix scenarios and cross-lever growth scorecard
- [x] Four scenario CSVs generated in `outputs/tables/` (gitignored, local only)
  - `margin_mix_opportunity.csv` — 26 rows, all categories with margin gap vs platform average
  - `scenario_margin_uplift.csv` — 3 rows, modeled margin gain from 1%/5%/10% mix shift
  - `growth_lever_scorecard.csv` — 11 rows, all levers ranked by impact × feasibility
  - `recommended_experiments.csv` — 3 rows, highest-priority actionable experiments

**Key findings:**
- All impact figures are cumulative over the full 2019–2026 dataset period; annualized columns added for clearer interpretation
- **Cart-to-purchase conversion** is the highest-upside lever: +5pp = **$503K cumulative / $68K annualized**; even +1pp = **$101K / $14K annualized**
- **Margin mix shift** has smaller upside than expected: a 10% shift from low-margin to margin-leader categories yields only **$34K cumulative / $4.6K annualized** — fashion demand is category-sticky and the margin gap is only ~11pp
- **Repeat purchase improvement** is a meaningful secondary lever: +10% more repeat orders = **$154K cumulative / $21K annualized**
- **Post-purchase improvements** have measurable upside but execution confidence is Low — root causes of the 15% cancellation rate and 10% return rate are not captured in the dataset
- Scorecard now separates **math confidence** (how well the arithmetic is supported by data) from **execution confidence** (how likely the scenario is achievable in practice)
- Top 3 recommended experiments: cart abandonment email A/B test, one-time buyer re-engagement campaign, cancellation root cause investigation

---

## Phase 5 — Post-Purchase Loss Analysis (Complete)

- [x] `src/build_post_purchase_analysis.py` created and committed — DuckDB queries against orders, order_items, products, inventory_items, distribution_centers
- [x] Five post-purchase CSVs generated in `outputs/tables/` (gitignored, local only)
  - `post_purchase_summary.csv` — 1 row, overall gross/net/cancelled/returned revenue and rates
  - `post_purchase_by_category.csv` — 26 rows, loss rates and margin impact per product category
  - `post_purchase_by_order_value.csv` — 4 rows, loss rates by order value band (< $50, $50–$99, $100–$199, $200+)
  - `post_purchase_by_customer_type.csv` — 2 rows, new vs repeat customer loss rates
  - `post_purchase_by_distribution_center.csv` — 10 rows, loss rates and delivery timing per DC
- [x] `src/create_post_purchase_charts.py` created and committed
- [x] Three post-purchase charts generated and committed in `outputs/figures/`
  - `post_purchase_revenue_loss_breakdown.png`
  - `post_purchase_rates_by_category.png`
  - `post_purchase_loss_by_order_value.png`

**Key findings:**
- Overall: **15.0% cancellation rate**, **9.9% return rate** — ~25% of all items lost post-purchase; **~$1.4M estimated margin impact**
- Loss rates are **flat across all 26 categories** (cancellation range: 13.8%–15.9%, return range: 8.1%–11.3%) — no category lever to pull
- Loss rates are **flat across all order value bands** — high-value orders cancel and return at the same rate as low-value orders
- Loss rates are **nearly identical for new vs repeat customers** (~15% cancel, ~10% return each) — not a new-customer onboarding problem
- Delivery timing is uniform across all 10 distribution centers (~0.5 days to ship, 2.5 days to deliver) — no DC outlier
- Post-purchase loss is a **platform-wide structural problem**, not a targetable segment or category issue

---

## Phase 4 — Conversion / Funnel Analysis (Complete)

- [x] `src/build_funnel_analysis.py` created and committed
- [x] Four funnel output CSVs generated in `outputs/tables/`
- [x] `src/create_funnel_charts.py` created and committed
- [x] Three funnel charts generated and committed in `outputs/figures/`
  - `funnel_stage_volumes_by_source.png`
  - `conversion_rates_by_source.png`
  - `funnel_overall_waterfall.png`

**Key findings:**
- Session purchase rate: **26.4%–27.0%** across all five traffic sources — flat regardless of channel
- Cart-to-purchase rate is ~**42%** — the drop-off (~58%) is the most significant funnel leak
- **Data caveat:** every session contains at least one product event, so browse-to-cart reflects cart eligibility, not true top-of-funnel drop-off

---

## Phase 3 — Product / Customer Value Analysis (Complete)

- [x] `src/build_product_value_analysis.py` created and committed — DuckDB queries against `data/processed/`, writes 5 output CSVs
- [x] Five product value CSVs generated in `outputs/tables/`
  - `product_category_value_ranking.csv` — 26 categories, revenue/margin/return/cancellation by category
  - `product_revenue_margin_quadrant.csv` — compact scatter dataset (net revenue, margin %, buyers)
  - `first_purchase_category_customer_value.csv` — LTV by first-purchase category (repeat rate, avg lifetime margin)
  - `first_vs_post_first_order_value.csv` — first vs post-first order margin split per first-purchase category
  - `product_category_recommendations.csv` — strategic role classification and recommendation note per category
- [x] `src/create_product_value_charts.py` created and committed — four portfolio charts
- [x] Four product value charts generated and committed in `outputs/figures/`
  - `first_vs_post_first_order_margin.png`
  - `lifetime_margin_vs_repeat_rate.png`
  - `revenue_margin_quadrant.png`
  - `strategic_role_counts.png`

**Key findings:**
- Repeat buyer rate is flat at ~37–39% across all 26 categories — repeat behavior is platform-level, not category-driven
- High-LTV categories (Outerwear & Coats $99, Suits & Sport Coats $93) are front-loaded: ~80% of lifetime margin comes from the first order
- Low-ticket replenishment categories (Socks, Underwear) have the most post-first durability (61–74% of LTV post-first) but very low absolute LTV
- Jeans is the largest margin leak: #2 in revenue ($949K) but 5+ points below average margin at 46.5%
- Blazers & Jackets is the highest-margin category (62.1%) but underscaled

---

## Local Data Workflow Setup (Complete)

- [x] Switched project workflow from BigQuery CLI to local Python/DuckDB
- [x] Raw BigQuery tables downloaded into `data/raw/` (7 tables, all present)
- [x] `src/clean_raw_csv_encoding.py` created and committed — decodes raw CSVs to clean UTF-8 in `data/processed/`
- [x] Clean UTF-8 processed copies generated in `data/processed/` (7 tables, all present)
- [x] `src/validate_raw_data.py` created and committed — validates processed files with DuckDB
- [x] Processed data validation passed: plain `read_csv_auto`, no `strict_mode` or `ignore_errors` workarounds
- [x] All 7 processed files readable, all row counts within 0.3% of reference
- [x] `data/` confirmed ignored by Git — raw and processed data never committed
- [x] Stale partial product value output from old BigQuery export workflow deleted
- [x] Core metric CSVs and figures remain intact

---

## Phase 2 — Core Business Metrics (Complete)

- [x] `sql/02_core_business_metrics.sql` created and committed
- [x] `scripts/run_core_business_metrics.ps1` created and committed
- [x] Core metric CSV outputs generated in `outputs/tables/`
  - `overall_business_summary.csv`
  - `monthly_business_metrics.csv`
  - `category_business_metrics.csv`
  - `customer_purchase_summary.csv`
  - `order_status_rates.csv`
- [x] `src/create_core_metric_charts.py` created and committed
- [x] Five core metric charts generated and committed in `outputs/figures/`
  - `monthly_gross_vs_net_revenue.png`
  - `top_categories_by_gross_revenue.png`
  - `top_categories_by_net_margin_pct.png`
  - `buyer_repeat_split.png`
  - `order_status_distribution.png`

---

## Next Actions

1. Create `PROJECT_PROGRESS.md` — a human-readable summary of all phases, findings, and recommendations for portfolio readers
2. Design A/B test recommendations — detailed experiment designs grounded in the scorecard findings
3. Begin Final Review and Project Defense (see phase below)

---

## Final Phase — Final Review and Project Defense (Not Started)

A structured three-pass audit before final GitHub polish. The goal is to stress-test the project as a portfolio artifact — catching overclaims, weak assumptions, and reproducibility gaps before a hiring manager or technical reviewer does.

### Pass 1 — Defender Pass

Make the strongest honest case for the project:
- What does the project demonstrate clearly and well?
- Which findings are tightly supported by the data?
- Which scripts and outputs are clean, reproducible, and well-structured?
- Where does the analysis go beyond surface-level observation?

### Pass 2 — Critic Pass

Challenge the project as a skeptical technical reviewer:
- **Assumptions:** Which analytical assumptions are too strong, unverified, or likely wrong? (Time period not normalized to annual; mix shift assumes transferable demand; marginal session treated as average session; etc.)
- **Overclaims:** Does any finding overstate certainty? Are any recommendations disconnected from what the data can actually support?
- **Weak findings:** Are any conclusions flat, obvious, or trivially explained by dataset construction (e.g., the flat funnel finding — is it a real business insight or a dataset artifact)?
- **Reproducibility gaps:** Can someone clone the repo and reproduce all outputs? Are `data/raw/` and `data/processed/` clearly documented as prerequisites? Are all script dependencies pinned?
- **Chart quality:** Are all charts labeled clearly enough for a standalone portfolio? Are any misleading or hard to interpret without context?
- **README gaps:** Does the README accurately describe what was found, not just what was built?

### Pass 3 — Reconciliation Pass

Produce a final punch list from Passes 1 and 2:
- List specific files, claims, or charts that need changes
- Distinguish: must-fix (correctness or major credibility issues) vs nice-to-fix (polish)
- Execute fixes in order of priority
- Final GitHub push with clean commit history

### Scope of the audit

| Area | What to check |
|---|---|
| `README.md` | Findings accurate, charts present, setup instructions complete |
| `src/*.py` | Scripts run cleanly from repo root; no hardcoded paths; dependencies in `requirements.txt` |
| `outputs/figures/` | All charts committed; labels readable; no misleading axes |
| `outputs/tables/` | Key CSVs described in README; columns self-explanatory |
| Assumptions | All scenario estimates clearly labeled as estimates, not measurements |
| Recommendations | Each recommended experiment grounded in a specific data finding |
| Time-period framing | All lever estimates clearly state they are cumulative over the dataset period, not annual |

---

## Open Questions

- Are traffic source / channel fields in the `events` table useful for segmentation (known ~no variation by channel in funnel rates)?
- Cohort analysis date range: dataset runs 2019–2026 with partial June 2026 data (exclude last 30–60 days for outcome-dependent metrics)

---

## Current Workflow

**As of 2026-06-05 the project has switched to a local raw data workflow.**

Reason: repeated terminal crashes and friction during BigQuery CLI exports made the prior bq-CLI-based workflow unreliable. The new approach downloads each raw table once and queries locally, making the workflow faster and fully reproducible without repeated cloud queries.

- **Data source:** BigQuery (`bigquery-public-data.thelook_ecommerce`) — authoritative, but queried only to download raw tables.
- **Raw data:** Downloaded once into `data/raw/` (one CSV per table). `data/` is Git-ignored and never committed.
- **Processed data:** Clean UTF-8 copies in `data/processed/` — generated by `src/clean_raw_csv_encoding.py`. This is the canonical query target.
- **Local query engine:** Python + DuckDB. All analysis queries run against `data/processed/`.
- **BigQuery CLI / console:** No longer the default analysis path. Used only if a new raw table needs to be pulled.
- **SQL files in `sql/`:** Retained as reference and documentation. New analysis queries will target local DuckDB.
- **Outputs:** Results that are part of project deliverables continue to be saved to `outputs/tables/` and `outputs/figures/`.
- **Direction and narrative:** ChatGPT for framing and interpretation; Claude Code for implementation.

---

## Important Rules for Future AI Sessions

- Always read PROJECT_PLAN.md and PROJECT_STATE.md before starting work
- Do not create new files, folders, notebooks, or scripts unless explicitly instructed
- Do not change project scope without explicit user approval
- Log tangents and ideas in IDEAS_BACKLOG.md — do not pursue them mid-session
- If stuck after 3 attempts, stop and summarize the blocker
- Keep this file concise — update it when asked, not speculatively
- The final narrative follows the data; do not force the starting hypothesis
