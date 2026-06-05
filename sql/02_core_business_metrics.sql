-- =============================================================================
-- 02_core_business_metrics.sql
-- Core business metric queries for the theLook eCommerce dataset
-- Dataset: bigquery-public-data.thelook_ecommerce
-- All queries are independently runnable in BigQuery Standard SQL
--
-- Revenue conventions used in this file:
--   gross_revenue       — SUM(order_items.sale_price) across all statuses
--   net_revenue         — SUM(order_items.sale_price) excluding Cancelled and Returned items
--   estimated_*_cost    — SUM(products.cost); catalog cost used as a proxy for COGS.
--                         Treat all cost and margin figures as estimates.
-- =============================================================================


-- =============================================================================
-- 1. OVERALL BUSINESS SUMMARY
-- One row summarizing the full dataset
-- Gross = all statuses; Net = excludes Cancelled and Returned
-- =============================================================================

SELECT
  COUNT(DISTINCT oi.order_id)                                                             AS total_orders,
  COUNT(DISTINCT oi.user_id)                                                              AS total_buyers,
  COUNT(oi.id)                                                                            AS total_items,

  -- Revenue
  ROUND(SUM(oi.sale_price), 2)                                                            AS gross_revenue,
  ROUND(SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price, 0)), 2)         AS net_revenue,

  -- Estimated cost
  ROUND(SUM(p.cost), 2)                                                                   AS estimated_gross_cost,
  ROUND(SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), p.cost, 0)), 2)                AS estimated_net_cost,

  -- Estimated gross margin (all statuses)
  ROUND(SUM(oi.sale_price) - SUM(p.cost), 2)                                              AS estimated_gross_margin,
  ROUND(
    SAFE_DIVIDE(SUM(oi.sale_price) - SUM(p.cost), SUM(oi.sale_price)) * 100,
    2
  )                                                                                        AS estimated_gross_margin_pct,

  -- Estimated net margin (excludes Cancelled and Returned)
  ROUND(SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price - p.cost, 0)), 2) AS estimated_net_margin,
  ROUND(
    SAFE_DIVIDE(
      SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price - p.cost, 0)),
      SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price, 0))
    ) * 100,
    2
  )                                                                                        AS estimated_net_margin_pct,

  -- Average order value
  ROUND(SAFE_DIVIDE(SUM(oi.sale_price), COUNT(DISTINCT oi.order_id)), 2)                  AS gross_avg_order_value,
  ROUND(
    SAFE_DIVIDE(
      SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price, 0)),
      COUNT(DISTINCT IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.order_id, NULL))
    ),
    2
  )                                                                                        AS net_avg_order_value

FROM
  `bigquery-public-data.thelook_ecommerce.order_items` AS oi
  INNER JOIN `bigquery-public-data.thelook_ecommerce.products` AS p
    ON oi.product_id = p.id;


-- =============================================================================
-- 2. MONTHLY BUSINESS METRICS
-- One row per calendar month (YYYY-MM)
-- Order month derived from order_items.created_at
-- Gross = all statuses; Net = excludes Cancelled and Returned
-- =============================================================================

SELECT
  FORMAT_DATE('%Y-%m', DATE(oi.created_at))                                                AS order_month,
  COUNT(DISTINCT oi.order_id)                                                              AS orders,
  COUNT(DISTINCT oi.user_id)                                                               AS buyers,
  COUNT(oi.id)                                                                             AS items_sold,

  -- Revenue
  ROUND(SUM(oi.sale_price), 2)                                                             AS gross_revenue,
  ROUND(SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price, 0)), 2)          AS net_revenue,

  -- Estimated gross margin (all statuses)
  ROUND(SUM(oi.sale_price) - SUM(p.cost), 2)                                               AS estimated_gross_margin,
  ROUND(
    SAFE_DIVIDE(SUM(oi.sale_price) - SUM(p.cost), SUM(oi.sale_price)) * 100,
    2
  )                                                                                         AS estimated_gross_margin_pct,

  -- Estimated net margin (excludes Cancelled and Returned)
  ROUND(SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price - p.cost, 0)), 2) AS estimated_net_margin,
  ROUND(
    SAFE_DIVIDE(
      SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price - p.cost, 0)),
      SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price, 0))
    ) * 100,
    2
  )                                                                                         AS estimated_net_margin_pct,

  -- Average order value
  ROUND(SAFE_DIVIDE(SUM(oi.sale_price), COUNT(DISTINCT oi.order_id)), 2)                   AS gross_avg_order_value,
  ROUND(
    SAFE_DIVIDE(
      SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price, 0)),
      COUNT(DISTINCT IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.order_id, NULL))
    ),
    2
  )                                                                                         AS net_avg_order_value

FROM
  `bigquery-public-data.thelook_ecommerce.order_items` AS oi
  INNER JOIN `bigquery-public-data.thelook_ecommerce.products` AS p
    ON oi.product_id = p.id
GROUP BY
  order_month
ORDER BY
  order_month;


-- =============================================================================
-- 3. CATEGORY BUSINESS METRICS
-- One row per product category
-- Gross = all statuses; Net = excludes Cancelled and Returned
-- avg_item_price = gross_revenue / items_sold (actual sale price, not catalog retail_price)
-- Return rate and cancellation rate use all items as denominator
-- =============================================================================

SELECT
  p.category,
  COUNT(oi.id)                                                                             AS items_sold,
  COUNT(DISTINCT oi.order_id)                                                              AS orders,
  COUNT(DISTINCT oi.user_id)                                                               AS buyers,

  -- Revenue
  ROUND(SUM(oi.sale_price), 2)                                                             AS gross_revenue,
  ROUND(SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price, 0)), 2)          AS net_revenue,

  -- Estimated gross margin (all statuses)
  ROUND(SUM(oi.sale_price) - SUM(p.cost), 2)                                               AS estimated_gross_margin,
  ROUND(
    SAFE_DIVIDE(SUM(oi.sale_price) - SUM(p.cost), SUM(oi.sale_price)) * 100,
    2
  )                                                                                         AS estimated_gross_margin_pct,

  -- Estimated net margin (excludes Cancelled and Returned)
  ROUND(SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price - p.cost, 0)), 2) AS estimated_net_margin,
  ROUND(
    SAFE_DIVIDE(
      SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price - p.cost, 0)),
      SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price, 0))
    ) * 100,
    2
  )                                                                                         AS estimated_net_margin_pct,

  -- Per-item price and outcome rates
  ROUND(SAFE_DIVIDE(SUM(oi.sale_price), COUNT(oi.id)), 2)                                  AS avg_item_price,
  ROUND(SAFE_DIVIDE(COUNTIF(oi.status = 'Returned'),  COUNT(oi.id)) * 100, 2)              AS return_rate,
  ROUND(SAFE_DIVIDE(COUNTIF(oi.status = 'Cancelled'), COUNT(oi.id)) * 100, 2)              AS cancellation_rate

FROM
  `bigquery-public-data.thelook_ecommerce.order_items` AS oi
  INNER JOIN `bigquery-public-data.thelook_ecommerce.products` AS p
    ON oi.product_id = p.id
GROUP BY
  p.category
ORDER BY
  gross_revenue DESC;


-- =============================================================================
-- 4. CUSTOMER PURCHASE SUMMARY
-- Aggregate buyer segmentation: one-time vs. repeat purchasers
-- Based on orders table; one row summary across all buyers
-- =============================================================================

WITH buyer_order_counts AS (
  SELECT
    user_id,
    COUNT(DISTINCT order_id) AS order_count
  FROM
    `bigquery-public-data.thelook_ecommerce.orders`
  GROUP BY
    user_id
)

SELECT
  COUNT(user_id)                                                                        AS total_buyers,
  COUNTIF(order_count = 1)                                                              AS one_time_buyers,
  COUNTIF(order_count >= 2)                                                             AS repeat_buyers,
  ROUND(SAFE_DIVIDE(COUNTIF(order_count >= 2), COUNT(user_id)) * 100, 2)               AS repeat_buyer_rate,
  ROUND(SAFE_DIVIDE(COUNTIF(order_count = 1),  COUNT(user_id)) * 100, 2)               AS one_time_buyer_rate,
  ROUND(SAFE_DIVIDE(SUM(order_count), COUNT(user_id)), 2)                               AS avg_orders_per_buyer,
  MAX(order_count)                                                                       AS max_orders_per_buyer
FROM
  buyer_order_counts;


-- =============================================================================
-- 5. ORDER STATUS RATES
-- One row per status, with count and share of total orders
-- Calculated at the order level from the orders table
-- =============================================================================

SELECT
  status,
  COUNT(order_id)                                                                       AS orders,
  ROUND(
    SAFE_DIVIDE(COUNT(order_id), SUM(COUNT(order_id)) OVER()) * 100,
    2
  )                                                                                     AS status_rate
FROM
  `bigquery-public-data.thelook_ecommerce.orders`
GROUP BY
  status
ORDER BY
  orders DESC;
