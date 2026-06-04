# Schema Discovery Notes — Phase 1
**Dataset:** `bigquery-public-data.thelook_ecommerce`
**Status:** Preliminary discovery notes. Not final conclusions.

---

## Table Row Counts

| Table | Row Count |
|---|---|
| users | 100,000 |
| orders | 125,408 |
| order_items | 181,815 |
| products | 29,120 |
| inventory_items | 489,994 |
| events | 2,429,781 |
| distribution_centers | 10 |

> Note: A `thelook_ecommerce-table` table exists in the dataset. Deferred — investigate later if relevant.

---

## Key Schema Observations

**events** — user_id, session_id, sequence_number, created_at, browser, traffic_source, uri, event_type

**users** — demographics, geography, traffic_source, created_at, user_geom

**orders** — order_id, user_id, status, gender, created_at, returned_at, shipped_at, delivered_at, num_of_item

**order_items** — order_id, user_id, product_id, inventory_item_id, status, timestamps, sale_price

**products** — cost, category, brand, retail_price, department, sku, distribution_center_id

**inventory_items** — product fields, cost, retail_price, sold_at, product_distribution_center_id

**distribution_centers** — id, name, latitude, longitude, geography

---

## Event Type Distribution

| Event Type | Count | % of Events |
|---|---|---|
| product | 844,711 | 34.76% |
| cart | 595,471 | 24.51% |
| department | 594,860 | 24.48% |
| purchase | 181,815 | 7.48% |
| cancel | 125,152 | 5.15% |
| home | 87,772 | 3.61% |

---

## Traffic Source Distribution (from events)

| Source | Events | Users | Sessions |
|---|---|---|---|
| Email | 1,091,950 | 52,199 | 306,562 |
| Adwords | 729,806 | 39,759 | 204,848 |
| Facebook | 245,253 | 16,327 | 68,482 |
| YouTube | 241,404 | 16,170 | 67,891 |
| Organic | 121,368 | 8,527 | 34,032 |

---

## Order Status Distribution

| Status | Orders | Order Items |
|---|---|---|
| Shipped | 37,563 | 54,437 |
| Complete | 31,204 | 45,293 |
| Processing | 25,055 | 36,353 |
| Cancelled | 18,881 | 27,306 |
| Returned | 12,705 | 18,426 |

---

## Session-Based Funnel by Traffic Source

| Source | Sessions | Browse-to-Cart | Cart-to-Purchase | Session Purchase Rate | Cancel-to-Purchase |
|---|---|---|---|---|---|
| Email | 306,562 | 63.41% | 41.99% | 26.62% | 68.87% |
| Adwords | 204,848 | 63.46% | 42.02% | 26.66% | 69.12% |
| Facebook | 68,482 | 63.61% | 42.18% | 26.83% | 68.55% |
| YouTube | 67,891 | 63.33% | 42.19% | 26.72% | 68.23% |
| Organic | 34,032 | 63.58% | 41.88% | 26.62% | 68.56% |

> **Note on cancel-to-purchase:** The `cancel` event type may not map cleanly to completed purchase sessions. This metric needs further investigation before use as a business conclusion.

---

## Analysis Viability Assessment

| Analysis Area | Viable? | Basis |
|---|---|---|
| Funnel analysis | Yes | events has session_id, traffic_source, event_type |
| Acquisition analysis | Yes | traffic_source exists in both events and users |
| Retention analysis | Yes | orders has user_id and created_at |
| Product performance | Yes | cost, category, brand, retail_price fields available |
| Fulfillment analysis | Yes | shipped_at, delivered_at, returned_at, status, inventory_items, distribution_centers all present |

---

## Early Implications

- Funnel conversion rates are strikingly similar across all five traffic sources (browse-to-cart ~63%, cart-to-purchase ~42%, session purchase rate ~27%). Channels differ primarily in acquisition volume, not early funnel efficiency — at least in this first pass.
- Email is the dominant channel by a wide margin: 52,199 users and 306,562 sessions vs. Organic's 8,527 users and 34,032 sessions.
- The `cancel` event type requires interpretation. It may represent a cancellation action within a session, not a session-level outcome. Do not use cancel-to-purchase as a primary metric until the event sequence logic is confirmed.
- All five planned analysis areas are confirmed viable based on available fields.

---

## Date Coverage and Freshness Notes

| Table | Field | Min | Max |
|---|---|---|---|
| orders | created_at | 2019-01-16 | 2026-06-04 |
| order_items | created_at | 2019-01-16 | 2026-06-08 |
| events | created_at | 2019-01-02 | 2026-06-08 |
| users | created_at | 2019-01-02 | 2026-06-03 |
| inventory_items | created_at | 2018-11-24 | 2026-06-07 |
| inventory_items | sold_at | 2019-01-16 | 2026-06-08 |

- `shipped_at`, `delivered_at`, and `returned_at` can extend several days beyond order/item creation timestamps.
- For fulfillment, return, and retention analyses, consider excluding the most recent 30–60 days to avoid incomplete outcome windows.
- The dataset appears synthetic but current through June 2026 — more modern than most public e-commerce datasets.

---

*These are preliminary schema discovery notes. All findings are subject to revision as deeper analysis proceeds.*
