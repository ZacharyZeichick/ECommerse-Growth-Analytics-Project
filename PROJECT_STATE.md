# Project State — E-Commerce Growth Analytics

*Living handoff document. Update this file at the end of every working session.*
*Last updated: 2026-06-05*

---

## Current Phase

**Phase 2 — Core Business Metrics** (visualization pass complete)

Next planned focus: **Product Value Analysis**

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

*Note: bq CLI is the working export path for now. Python BigQuery connection not yet tested.*

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

1. Begin Product Value Analysis (next planned focus)

---

## Open Questions

- Are traffic source / channel fields in the `events` table useful for segmentation (known ~no variation by channel in funnel rates)?
- Cohort analysis date range: dataset runs 2019–2026 with partial June 2026 data (exclude last 30–60 days for outcome-dependent metrics)

---

## Current Workflow

- Claude Code / terminal is the main build environment.
- Use the BigQuery CLI to run saved SQL queries when practical.
- The BigQuery website can be used for quick inspection or debugging, but is not the default workflow.
- SQL should live in the repo before being used for repeatable analysis.
- Query outputs that are part of project deliverables should be saved to `outputs/tables/`.
- Use ChatGPT for analysis direction, interpretation, and narrative decisions.

---

## Important Rules for Future AI Sessions

- Always read PROJECT_PLAN.md and PROJECT_STATE.md before starting work
- Do not create new files, folders, notebooks, or scripts unless explicitly instructed
- Do not change project scope without explicit user approval
- Log tangents and ideas in IDEAS_BACKLOG.md — do not pursue them mid-session
- If stuck after 3 attempts, stop and summarize the blocker
- Keep this file concise — update it when asked, not speculatively
- The final narrative follows the data; do not force the starting hypothesis
