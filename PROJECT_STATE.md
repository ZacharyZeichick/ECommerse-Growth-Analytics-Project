# Project State — E-Commerce Growth Analytics

*Living handoff document. Update this file at the end of every working session.*
*Last updated: 2026-06-05 (post product value analysis)*

---

## Current Phase

**Product / Customer Value Analysis complete**

Next planned focus: **Acquisition or Conversion analysis** — confirm direction with ChatGPT framing before starting

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

## In-Progress Work

- Nothing currently in progress

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

1. Confirm next analysis phase with ChatGPT framing (Acquisition or Conversion)
2. New analysis scripts go in `src/` and query `data/processed/` — do not use BigQuery or PowerShell export scripts
3. Outputs go to `outputs/tables/` (CSV) and `outputs/figures/` (PNG) as before

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
