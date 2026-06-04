# Metric Definitions — E-Commerce Growth Analytics
**Dataset:** `bigquery-public-data.thelook_ecommerce`
**Status:** Working definitions for this project. Update if data discoveries require revision.

---

## Modeling Notes (Apply Project-Wide)

| Rule | Rationale |
|---|---|
| Use `users.traffic_source` for acquisition analysis | Represents the channel that originally acquired the user |
| Use `events.traffic_source` for session/funnel analysis | Represents the channel for a specific session or event |
| Use `session_id` as the funnel unit | ~46% of `events.user_id` values are null; session_id is fully populated |
| Use `orders.user_id` / `order_items.user_id` for retention and customer value | These fields are fully populated and user-attributed |
| Treat margin as an estimate | `products.cost` is a proxy; actual cost may differ |
| First-purchase category is an association, not a cause | Customer intent and demographics co-vary with category |
| Exclude or flag the most recent 30–60 days for return, delivery, and retention analysis | Outcome windows may be incomplete for recent orders |
| Never use raw event counts as conversion rates | Use session-level or user-level denominators |

---

## Revenue Metrics

### Revenue
**Definition:** Total sale price of completed or shipped order items. Excludes cancelled and returned items unless otherwise specified.

**Tables:** `order_items`

**Formula:**
```sql
SUM(sale_price)
-- Filter: WHERE status NOT IN ('Cancelled', 'Returned')
-- or WHERE status IN ('Complete', 'Shipped') depending on analysis scope
```

**Notes:** `sale_price` has zero nulls across 181,815 rows. Always document which statuses are included.

---

### Estimated Cost
**Definition:** The product cost associated with sold items, used as a proxy for cost of goods sold.

**Tables:** `order_items`, `products`

**Formula:**
```sql
SUM(p.cost)
-- Join: order_items oi JOIN products p ON oi.product_id = p.id
```

**Notes:** `products.cost` is the catalog cost, not a transaction-level cost. Treat as an estimate.

---

### Estimated Gross Margin
**Definition:** Revenue minus estimated cost.

**Tables:** `order_items`, `products`

**Formula:**
```sql
SUM(oi.sale_price) - SUM(p.cost)
```

---

### Estimated Margin Percentage
**Definition:** Estimated gross margin as a percentage of revenue.

**Formula:**
```sql
ROUND(SAFE_DIVIDE(SUM(oi.sale_price) - SUM(p.cost), SUM(oi.sale_price)) * 100, 2)
```

**Notes:** Use `SAFE_DIVIDE` to avoid division-by-zero errors. Margin percentages vary across categories (~40%–62% observed in discovery).

---

### Average Order Value (AOV)
**Definition:** Average revenue per order, calculated at the order level.

**Tables:** `order_items`, `orders`

**Formula:**
```sql
ROUND(SAFE_DIVIDE(SUM(oi.sale_price), COUNT(DISTINCT oi.order_id)), 2)
-- Filter on desired statuses
```

**Notes:** Calculate at order level (not item level) to avoid inflating AOV for multi-item orders.

---

## Customer Metrics

### Buyer
**Definition:** A user who has placed at least one order.

**Tables:** `orders`

**Formula:**
```sql
COUNT(DISTINCT user_id) -- from orders
```

---

### One-Time Buyer
**Definition:** A user who has placed exactly one order.

**Tables:** `orders`

**Formula:**
```sql
COUNT(DISTINCT user_id)
-- From a subquery where COUNT(order_id) per user = 1
```

---

### Repeat Buyer
**Definition:** A user who has placed two or more orders.

**Tables:** `orders`

**Formula:**
```sql
COUNT(DISTINCT user_id)
-- From a subquery where COUNT(order_id) per user >= 2
```

---

### Repeat Buyer Rate
**Definition:** Share of buyers who made more than one purchase.

**Formula:**
```sql
ROUND(SAFE_DIVIDE(COUNT(DISTINCT repeat_buyers), COUNT(DISTINCT all_buyers)) * 100, 2)
```

**Notes:** Observed overall rate is 37.75%. Maximum orders per user observed is 4.

---

## Funnel Metrics

### Session
**Definition:** A distinct browsing session identified by `session_id` in the events table.

**Tables:** `events`

**Formula:**
```sql
COUNT(DISTINCT session_id)
```

**Notes:** Use `session_id` as the funnel unit. Do not use `user_id` because ~46% of event rows have null `user_id`.

---

### Browse Session
**Definition:** A session that contains at least one `product` or `department` event.

**Tables:** `events`

**Formula:**
```sql
COUNT(DISTINCT session_id)
WHERE event_type IN ('product', 'department')
```

---

### Cart Session
**Definition:** A session that contains at least one `cart` event.

**Tables:** `events`

**Formula:**
```sql
COUNT(DISTINCT session_id)
WHERE event_type = 'cart'
```

---

### Purchase Session
**Definition:** A session that contains at least one `purchase` event.

**Tables:** `events`

**Formula:**
```sql
COUNT(DISTINCT session_id)
WHERE event_type = 'purchase'
```

---

### Browse-to-Cart Rate
**Definition:** Share of browse sessions that also contain a cart event.

**Formula:**
```sql
ROUND(SAFE_DIVIDE(cart_sessions, browse_sessions) * 100, 2)
```

**Notes:** Observed rates are ~63% across all traffic sources in discovery — little variation by channel.

---

### Cart-to-Purchase Rate
**Definition:** Share of cart sessions that also contain a purchase event.

**Formula:**
```sql
ROUND(SAFE_DIVIDE(purchase_sessions, cart_sessions) * 100, 2)
```

**Notes:** Observed rates are ~42% across traffic sources in discovery.

---

### Session Purchase Rate
**Definition:** Share of all sessions that contain a purchase event.

**Formula:**
```sql
ROUND(SAFE_DIVIDE(purchase_sessions, total_sessions) * 100, 2)
```

**Notes:** Observed rates are ~27% across traffic sources in discovery.

---

## Post-Purchase Metrics

### Return Rate
**Definition:** Share of order items (or orders) with a `Returned` status.

**Tables:** `order_items` or `orders`

**Formula:**
```sql
ROUND(SAFE_DIVIDE(
  COUNTIF(status = 'Returned'),
  COUNT(*)
) * 100, 2)
```

**Notes:** Exclude recent 30–60 days when analyzing return rates to avoid incomplete outcome windows. Observed overall rate is approximately 10%.

---

### Cancellation Rate
**Definition:** Share of order items (or orders) with a `Cancelled` status.

**Tables:** `order_items` or `orders`

**Formula:**
```sql
ROUND(SAFE_DIVIDE(
  COUNTIF(status = 'Cancelled'),
  COUNT(*)
) * 100, 2)
```

**Notes:** Exclude recent 30–60 days. Observed overall rate is approximately 14–16%.

---

## Customer Value Metrics

### First Purchase Category
**Definition:** The product category of a user's earliest order item by `created_at`.

**Tables:** `order_items`, `products`

**Formula:**
```sql
-- Use ROW_NUMBER() or RANK() partitioned by user_id, ordered by created_at ASC
-- Take the category from the row ranked 1
```

**Notes:** Treat as an association with downstream customer value, not a causal claim. Customer demographics and intent co-vary with category choice.

---

### Average Lifetime Revenue
**Definition:** Average total revenue per buyer across all of their orders.

**Tables:** `order_items`

**Formula:**
```sql
ROUND(SAFE_DIVIDE(SUM(sale_price), COUNT(DISTINCT user_id)), 2)
-- Aggregated at the user level first, then averaged
```

**Notes:** Observed range by first-purchase category: ~$34 (Socks & Hosiery) to ~$240 (Outerwear & Coats) average lifetime margin.

---

### Average Lifetime Margin
**Definition:** Average estimated gross margin per buyer across all of their orders.

**Tables:** `order_items`, `products`

**Formula:**
```sql
ROUND(SAFE_DIVIDE(SUM(oi.sale_price - p.cost), COUNT(DISTINCT oi.user_id)), 2)
```

**Notes:** Subject to the same estimation caveats as Estimated Gross Margin above.
