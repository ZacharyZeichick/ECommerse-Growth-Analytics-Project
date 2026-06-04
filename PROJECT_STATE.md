# Project State — E-Commerce Growth Analytics

*Living handoff document. Update this file at the end of every working session.*
*Last updated: 2026-06-04*

---

## Current Phase

**Phase 0 — Project Setup** (in progress)

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

## Next Actions

1. Confirm BigQuery access (console and/or Python)
2. Run schema exploration queries across all key tables
3. Document row counts, date ranges, null rates, and key cardinality
4. Define and document the core metric set (conversion rate, LTV, repeat rate, return rate)
5. Create initial SQL exploration queries after BigQuery access is confirmed

---

## Open Questions

- Is BigQuery access available via service account or ADC (Application Default Credentials)?
- Are cost/margin fields available in the dataset, or will analysis be revenue-only?
- What date range does the dataset cover? (Need to confirm before cohort analysis)
- Are traffic source / channel fields populated in the `events` table?

---

## Important Rules for Future AI Sessions

- Always read PROJECT_PLAN.md and PROJECT_STATE.md before starting work
- Do not create new files, folders, notebooks, or scripts unless explicitly instructed
- Do not change project scope without explicit user approval
- Log tangents and ideas in IDEAS_BACKLOG.md — do not pursue them mid-session
- If stuck after 3 attempts, stop and summarize the blocker
- Keep this file concise — update it when asked, not speculatively
- The final narrative follows the data; do not force the starting hypothesis
