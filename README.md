# E-Commerce Growth Analytics

**End-to-end analytics portfolio project identifying where an e-commerce business leaks growth — across product mix, customer value, acquisition, conversion, retention, and fulfillment.**

Dataset: [theLook eCommerce](https://console.cloud.google.com/marketplace/product/bigquery-public-data/thelook-ecommerce) (Google BigQuery public dataset) — 125,408 orders, 100,000 users, 29,120 products.

> **Note on the dataset:** theLook eCommerce is a synthetic dataset. Revenue figures and trends reflect how the dataset was constructed, not observed real-world business performance. In particular, the accelerating revenue growth visible in 2025–2026 is a property of the synthetic data, not evidence of a real business event.

---

## Core Business Question

> *"Where is this e-commerce business leaking growth: acquisition, conversion, retention, product mix, or fulfillment?"*

---

## Project Status

| Workstream | Status | Assets | Key Finding / Next Step |
|---|---|---|---|
| Data workflow | Complete | 7 processed tables; local DuckDB pipeline | No repeated cloud queries; all analysis runs against `data/processed/` |
| Core business metrics | Complete | 5 charts | ~25% order loss rate (cancel + return); 37.7% repeat buyer rate |
| Product / customer value | Complete | 4 charts | Jeans is the largest margin leak; Blazers & Jackets is highest-margin and underscaled |
| Funnel analysis | Complete | 3 charts | ~26.5% session-purchase rate flat across all 5 channels; 58% cart abandonment is the primary conversion leak |
| Post-purchase loss | Complete | 3 charts | 15% cancel rate, 10% return rate — flat across all categories, order value bands, and customer types; structural platform problem |
| Margin mix scenarios | Complete | Growth lever scorecard; 4 CSVs | Cart-to-purchase conversion is the highest-upside lever (~$68K/yr annualized); pure margin mix shift has smaller upside than expected (~$4.6K/yr for a 10% shift) |
| A/B test design | Complete | 3 experiment CSVs | Cart abandonment recovery is top-priority; one-time buyer reactivation is second; cancellation work starts with reason-capture instrumentation |
| Unit economics waterfall | Complete | 1 waterfall chart | Gross revenue of $10.86M becomes $4.23M estimated net margin after cancellations, returns, and estimated product cost |
| Tableau / dashboard | Not started | — | Visual portfolio layer |
| Final review / defense | In progress | — | Defender + critic + reconciliation passes before final polish |

---

## Tools & Workflow

| Tool | Role |
|------|------|
| BigQuery | Raw data source |
| Python + DuckDB | Local SQL analysis against downloaded CSVs |
| pandas + matplotlib | Data wrangling and visualization |
| GitHub | Version control and portfolio presentation |

Raw tables are downloaded once from BigQuery into `data/` (git-ignored) and queried locally via DuckDB — no repeated cloud queries needed.

---

## Reproducing This Project

**Prerequisites:** Python 3.10+, a Google Cloud project with BigQuery access to `bigquery-public-data.thelook_ecommerce`.

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download the 7 raw tables from BigQuery into data/raw/
#    Tables: orders, order_items, users, products, events,
#            inventory_items, distribution_centers
#    Export each as CSV from the BigQuery console or bq CLI.

# 3. Clean encoding and validate
python src/clean_raw_csv_encoding.py
python src/validate_raw_data.py

# 4. Core business metric CSVs (Phase 2)
#    Run sql/02_core_business_metrics.sql in BigQuery and download
#    the 5 result CSVs into outputs/tables/:
#      overall_business_summary.csv, monthly_business_metrics.csv,
#      category_business_metrics.csv, customer_purchase_summary.csv,
#      order_status_rates.csv
#    Column names must match those defined in sql/02_core_business_metrics.sql exactly;
#    BigQuery exports may need to be renamed if headers are auto-formatted on download.
python src/create_core_metric_charts.py

# 5. Product / customer value analysis
python src/build_product_value_analysis.py
python src/create_product_value_charts.py

# 6. Funnel analysis
python src/build_funnel_analysis.py
python src/create_funnel_charts.py

# 7. Post-purchase loss analysis
python src/build_post_purchase_analysis.py
python src/create_post_purchase_charts.py

# 8. Margin mix scenarios and growth lever scorecard
#    (requires outputs from steps 5, 6, 7)
python src/build_margin_mix_scenarios.py

# 9. A/B experiment designs
#    (requires outputs from steps 5, 6, 7, 8)
python src/build_experiment_recommendations.py

# 10. Unit economics waterfall chart
#     (requires outputs from steps 7, 8)
python src/create_unit_economics_waterfall.py
```

All chart outputs write to `outputs/figures/`. All intermediate CSV outputs write to `outputs/tables/` (git-ignored; local only).

---

## Analyses

### Phase 1 — Core Business Metrics

High-level health check across revenue, margin, category performance, and customer behavior.

**Monthly Gross vs Net Revenue**
Revenue has grown consistently since 2019. The gap between gross and net (cancelled + returned orders) is stable at ~25%, indicating a structural fulfillment issue rather than a growing one.

![Monthly Revenue](outputs/figures/monthly_gross_vs_net_revenue.png)

**Top Categories by Gross Revenue**
Outerwear & Coats, Jeans, and Sweaters are the three largest revenue drivers.

![Top Categories Revenue](outputs/figures/top_categories_by_gross_revenue.png)

**Top Categories by Net Margin %**
Blazers & Jackets (62%), Accessories (60%), and Skirts (60%) are the most margin-efficient categories — but all three are significantly underscaled relative to their margins.

![Top Categories Margin](outputs/figures/top_categories_by_net_margin_pct.png)

**Repeat vs One-Time Buyers**
Only 37.7% of customers make more than one purchase. The majority of revenue comes from one-time buyers, making acquisition costs difficult to recover.

![Buyer Repeat Split](outputs/figures/buyer_repeat_split.png)

**Order Status Distribution**
~10% of orders are returned and ~15% are cancelled — a combined ~25% loss rate that directly compresses net revenue and margin. "Shipped" and "Processing" orders represent in-flight orders at the time of the dataset snapshot.

![Order Status](outputs/figures/order_status_distribution.png)

---

### Phase 2 — Product / Customer Value Analysis

Deep dive into which categories generate the most customer lifetime value, and whether that value is durable after the first order.

**Revenue vs Margin Quadrant**
Each bubble is a product category, sized by number of buyers, colored by strategic role. Revenue leaders (blue) sit top-right; Low-margin volume categories (amber) are high-revenue but margin-dilutive.

![Revenue Margin Quadrant](outputs/figures/revenue_margin_quadrant.png)

**First vs Post-First Order Margin**
The top 10 categories by lifetime margin, split into first-order margin (dark blue) and post-first-order margin (light blue). High-ticket categories like Outerwear & Coats are heavily front-loaded — ~80% of lifetime margin comes from the first purchase.

![First vs Post-First Margin](outputs/figures/first_vs_post_first_order_margin.png)

**Lifetime Margin vs Repeat Rate**
Repeat buyer rate is nearly flat across all 26 categories (36–39%). Category choice does not drive repeat behavior — retention is a platform-level problem, not a product mix problem.

![Lifetime Margin vs Repeat Rate](outputs/figures/lifetime_margin_vs_repeat_rate.png)

**Category Count by Strategic Role**
Summary of how the 26 categories distribute across strategic roles based on revenue, margin, and LTV signals.

![Strategic Role Counts](outputs/figures/strategic_role_counts.png)

---

### Phase 3 — Funnel Analysis

Session-level conversion analysis across all five traffic sources using the `events` table.

> **Data caveat:** Every session in this dataset contains at least one product-page view event. As a result, the browse-to-cart rate measures conversion among sessions that already reached a product page — it is not a true top-of-funnel drop-off rate. The cart-to-purchase rate is unaffected by this limitation.

**Funnel Stage Volumes by Traffic Source**
Email is the largest traffic source by session volume. All five channels (Email, Adwords, YouTube, Facebook, Organic) follow a similar funnel shape.

![Funnel Volumes](outputs/figures/funnel_stage_volumes_by_source.png)

**Conversion Rates by Traffic Source**
Browse-to-cart (~63%) and cart-to-purchase (~42%) rates are flat across all five channels. There is no channel-specific conversion problem — funnel performance is uniform platform-wide.

![Conversion Rates](outputs/figures/conversion_rates_by_source.png)

**Overall Purchase Funnel — Session Drop-Off**
Of 681,667 total sessions, 432,099 (63%) added to cart. Of those, only 181,667 (42%) completed a purchase. The 58% cart abandonment rate is the primary conversion leak.

![Funnel Waterfall](outputs/figures/funnel_overall_waterfall.png)

---

### Phase 4 — Post-Purchase Loss Analysis

Cancellation and return rates analyzed by category, order value, customer type, and distribution center.

**Gross Revenue Breakdown**
Of $10.86M gross revenue, $1.63M (15.0%) was lost to cancellations and $1.07M (9.9%) to returns — a combined $2.7M post-purchase revenue loss.

![Revenue Loss Breakdown](outputs/figures/post_purchase_revenue_loss_breakdown.png)

**Post-Purchase Loss Rates by Category**
Cancellation (13.8%–15.9%) and return (8.1%–11.3%) rates are nearly identical across all 26 categories. There is no category lever to pull — this is a platform-wide structural problem.

![Rates by Category](outputs/figures/post_purchase_rates_by_category.png)

**Post-Purchase Loss Rates by Order Value**
Loss rates are flat across all order value bands (< $50 through $200+). High-value orders cancel and return at the same rate as low-value orders.

![Loss by Order Value](outputs/figures/post_purchase_loss_by_order_value.png)

Additional cuts (not charted) confirm: new and repeat customers cancel and return at identical rates (~15% / ~10%), and all 10 distribution centers show uniform delivery timing and loss rates.

---

### Phase 5 — Margin Mix Scenario Analysis

Scenario modeling of five growth levers: margin mix shift, cart-to-purchase conversion, repeat purchase improvement, cancellation reduction, and return reduction. All impact figures are cumulative over the full 2019–2026 dataset period; annualized figures divide by 7.4 years.

| Lever | Scenario | Annualized Margin Upside | Math Confidence | Execution Confidence |
|---|---|---|---|---|
| Cart-to-purchase +1pp | +1pp conversion rate | ~$14K/yr | High | Medium |
| Cart-to-purchase +5pp | +5pp conversion rate | ~$68K/yr | High | Low |
| Repeat orders +5% | +5% more repeat purchases | ~$10K/yr | Medium | Medium |
| Repeat orders +10% | +10% more repeat purchases | ~$21K/yr | Medium | Low |
| Cancellation rate −1pp | Recover 1pp of cancelled items | ~$8K/yr | High | Low |
| Return rate −1pp | Recover 1pp of returned items | ~$8K/yr | High | Low |
| Margin mix shift 10% | Shift 10% of low-margin to high-margin | ~$5K/yr | Medium | Low |

The full scorecard with assumption notes and feasibility ratings is in `outputs/tables/growth_lever_scorecard.csv`.

---

### Phase 6 — A/B Test Design

Four experiment designs grounded in the growth lever scorecard, each with hypothesis, target segment, control/treatment definition, primary metric, guardrail metrics, upside estimate, and risk caveats.

| ID | Experiment | Lever | Annualized Upside | Launch Priority |
|---|---|---|---|---|
| EXP-001 | Cart abandonment recovery email | Conversion | ~$14K/yr | 1st |
| EXP-002 | One-time buyer reactivation campaign | Retention | ~$10K/yr | 2nd |
| EXP-004 | Cancellation reason capture (Phase A instrumentation) | Post-purchase | ~$8K/yr (Phase B) | 3rd |
| EXP-003 | High-margin category merchandising test | Product mix | ~$456/yr | 4th |

EXP-004 is instrumentation-first: the cancellation rate is flat across all segments, meaning the root cause is unknown. Phase A (add a reason-selection step to the cancel flow) must precede any intervention design.

Full experiment designs are in `outputs/tables/experiment_designs.csv`. Metric definitions (4 primary, 9 guardrail) are in `outputs/tables/experiment_metric_definitions.csv`.

---

### Unit Economics Waterfall

Single executive visual tracing $10.86M gross revenue to $4.23M estimated net margin.

Product cost is estimated using the platform blended margin rate of 51.9% (weighted average derived from actual product cost data across all 26 categories).

![Unit Economics Waterfall](outputs/figures/unit_economics_waterfall.png)

---

## Key Findings

| Finding | Implication |
|---------|-------------|
| ~25% of orders cancelled or returned | Structural fulfillment or expectation-setting problem — compresses margin across all categories |
| 37.7% repeat buyer rate, flat across all categories | Retention is a platform issue, not a product mix issue — no category is "sticky" |
| Outerwear & Coats: $99 avg lifetime margin but 80% front-loaded | High-LTV acquisition target, but the business doesn't benefit much from repeat purchasing |
| Jeans: #2 in revenue ($949K) but 5+ points below average margin | Largest single margin leak in the catalog |
| Blazers & Jackets: highest margin % (62%) but underscaled | Scaling this category would improve the overall margin mix |
| Socks / Underwear: 61–74% of LTV comes post-first-order | Most durable categories, but absolute LTV is low ($24–35) |
| 58% cart abandonment rate; flat across all 5 traffic channels | Cart-to-purchase conversion is the highest-ROI lever; channel mix does not explain the drop-off |
| Post-purchase loss rates flat across all 26 categories, all order value bands, new vs. repeat customers, and all 10 distribution centers | No targetable segment or category lever — this requires a root-cause investigation (reason capture), not a targeted intervention |
| Cart-to-purchase +1pp = ~$14K/yr annualized margin upside; +5pp = ~$68K/yr | Highest-confidence, highest-feasibility growth lever |
| Pure margin mix shift has limited upside: 10% shift = ~$5K/yr | Fashion demand is category-sticky; a mix-shift test is a learning experiment, not a margin program |
| Gross revenue of $10.86M → $4.23M estimated net margin (39% of gross) | Cancellations + returns + product cost consume 61% of gross revenue |

---

## Repository Structure

```
├── sql/                            # Reference SQL (BigQuery syntax)
│   └── 02_core_business_metrics.sql
├── src/                            # Python scripts — analysis and charts
│   ├── clean_raw_csv_encoding.py       # Decode raw BigQuery CSVs to clean UTF-8
│   ├── validate_raw_data.py            # Validate processed files with DuckDB
│   ├── create_core_metric_charts.py    # Core business metric charts (Phase 1)
│   ├── build_product_value_analysis.py # Product / customer value queries (Phase 2)
│   ├── create_product_value_charts.py  # Product value charts (Phase 2)
│   ├── build_funnel_analysis.py        # Funnel / conversion queries (Phase 3)
│   ├── create_funnel_charts.py         # Funnel charts (Phase 3)
│   ├── build_post_purchase_analysis.py # Post-purchase loss queries (Phase 4)
│   ├── create_post_purchase_charts.py  # Post-purchase charts (Phase 4)
│   ├── build_margin_mix_scenarios.py   # Margin mix scenarios + growth lever scorecard (Phase 5)
│   ├── build_experiment_recommendations.py  # A/B experiment designs (Phase 6)
│   └── create_unit_economics_waterfall.py   # Unit economics waterfall chart
├── outputs/
│   ├── tables/              # CSV outputs from each analysis (git-ignored; local only)
│   └── figures/             # PNG charts (committed)
├── reports/                 # Metric definitions and reference docs
├── PROJECT_PLAN.md          # Full project scope and phase definitions
├── PROJECT_STATE.md         # Living handoff doc — current status and next steps
└── requirements.txt
```

> `data/` is git-ignored. Raw and processed CSVs live locally only. `outputs/tables/` is also git-ignored; only chart PNGs are committed.

See [`reports/metric_definitions.md`](reports/metric_definitions.md) for definitions of all computed metrics and the revenue conventions (gross vs. net, estimated margin) used across analyses.
