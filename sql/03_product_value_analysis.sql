-- =============================================================================
-- 03_product_value_analysis.sql
-- Product value analysis queries for the theLook eCommerce dataset
-- Dataset: bigquery-public-data.thelook_ecommerce
-- All queries are independently runnable in BigQuery Standard SQL
--
-- Revenue conventions (consistent with 02_core_business_metrics.sql):
--   gross_revenue            — SUM(order_items.sale_price) across all statuses
--   net_revenue              — SUM(order_items.sale_price) excluding Cancelled and Returned
--   estimated_net_margin     — SUM(sale_price - products.cost) excluding Cancelled and Returned
--   estimated_net_margin_pct — estimated_net_margin / net_revenue * 100
--
-- First-purchase category convention:
--   Each user's first purchase category is derived from the earliest order by
--   orders.created_at. If a first order spans multiple categories, the category
--   with the highest total sale_price in that order is assigned. Alphabetical
--   order on category name is used as a deterministic tiebreaker.
--   Treat all first-purchase category findings as associations — customer
--   demographics and intent co-vary with category choice.
-- =============================================================================


-- =============================================================================
-- 1. CATEGORY REVENUE AND MARGIN RANKING
-- One row per product category
-- Gross = all statuses; Net = excludes Cancelled and Returned
-- avg_item_price  = gross_revenue / items_sold (actual sale price, not catalog price)
-- return_rate and cancellation_rate use all items as denominator
-- Ordered by net_revenue descending
-- =============================================================================

SELECT
  p.category,
  COUNT(oi.id)                                                                               AS items_sold,
  COUNT(DISTINCT oi.order_id)                                                                AS orders,
  COUNT(DISTINCT oi.user_id)                                                                 AS buyers,

  -- Revenue
  ROUND(SUM(oi.sale_price), 2)                                                               AS gross_revenue,
  ROUND(SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price, 0)), 2)            AS net_revenue,

  -- Estimated net margin (excludes Cancelled and Returned)
  ROUND(
    SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price - p.cost, 0)),
    2
  )                                                                                           AS estimated_net_margin,
  ROUND(
    SAFE_DIVIDE(
      SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price - p.cost, 0)),
      SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price, 0))
    ) * 100,
    2
  )                                                                                           AS estimated_net_margin_pct,

  -- Per-item price and outcome rates
  ROUND(SAFE_DIVIDE(SUM(oi.sale_price), COUNT(oi.id)), 2)                                    AS avg_item_price,
  ROUND(SAFE_DIVIDE(COUNTIF(oi.status = 'Returned'),  COUNT(oi.id)) * 100, 2)                AS return_rate,
  ROUND(SAFE_DIVIDE(COUNTIF(oi.status = 'Cancelled'), COUNT(oi.id)) * 100, 2)                AS cancellation_rate

FROM
  `bigquery-public-data.thelook_ecommerce.order_items` AS oi
  INNER JOIN `bigquery-public-data.thelook_ecommerce.products` AS p
    ON oi.product_id = p.id
GROUP BY
  p.category
ORDER BY
  net_revenue DESC;


-- =============================================================================
-- 2. REVENUE VS MARGIN QUADRANT DATASET
-- One row per product category
-- Designed to support a scatter plot: net_revenue on one axis,
-- estimated_net_margin_pct on the other, with buyers as bubble size
-- All categories included; no minimum revenue filter
-- =============================================================================

SELECT
  p.category,
  ROUND(SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price, 0)), 2)            AS net_revenue,
  ROUND(
    SAFE_DIVIDE(
      SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price - p.cost, 0)),
      SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price, 0))
    ) * 100,
    2
  )                                                                                           AS estimated_net_margin_pct,
  COUNT(DISTINCT oi.user_id)                                                                 AS buyers,
  COUNT(oi.id)                                                                               AS items_sold,
  ROUND(SAFE_DIVIDE(SUM(oi.sale_price), COUNT(oi.id)), 2)                                    AS avg_item_price

FROM
  `bigquery-public-data.thelook_ecommerce.order_items` AS oi
  INNER JOIN `bigquery-public-data.thelook_ecommerce.products` AS p
    ON oi.product_id = p.id
GROUP BY
  p.category
ORDER BY
  net_revenue DESC;


-- =============================================================================
-- 3. FIRST PURCHASE CATEGORY CUSTOMER VALUE
-- One row per first-purchase category
--
-- Step 1: Rank each user's orders by orders.created_at to find order rank = 1
-- Step 2: Among items in that first order, assign the category with the
--         highest total sale_price (alphabetical tiebreaker)
-- Step 3: Compute lifetime revenue and lifetime margin from ALL order_items
--         across each user's full order history (net: excludes Cancelled/Returned)
-- Step 4: Aggregate by first_purchase_category
-- =============================================================================

WITH ranked_orders AS (
  SELECT
    user_id,
    order_id,
    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at ASC) AS order_rank
  FROM
    `bigquery-public-data.thelook_ecommerce.orders`
),

first_order_ids AS (
  SELECT user_id, order_id
  FROM ranked_orders
  WHERE order_rank = 1
),

first_order_categories AS (
  -- Revenue per category within each user's first order
  SELECT
    foi.user_id,
    p.category,
    SUM(oi.sale_price) AS category_revenue_in_first_order
  FROM
    first_order_ids AS foi
    INNER JOIN `bigquery-public-data.thelook_ecommerce.order_items` AS oi
      ON foi.order_id = oi.order_id
    INNER JOIN `bigquery-public-data.thelook_ecommerce.products` AS p
      ON oi.product_id = p.id
  GROUP BY
    foi.user_id, p.category
),

user_first_category AS (
  -- Pick the dominant category; category name breaks ties deterministically
  SELECT user_id, category AS first_purchase_category
  FROM (
    SELECT
      user_id,
      category,
      ROW_NUMBER() OVER (
        PARTITION BY user_id
        ORDER BY category_revenue_in_first_order DESC, category ASC
      ) AS cat_rank
    FROM first_order_categories
  )
  WHERE cat_rank = 1
),

user_lifetime AS (
  -- Lifetime order count, revenue, and margin per user (net basis)
  SELECT
    oi.user_id,
    COUNT(DISTINCT oi.order_id)                                                              AS lifetime_orders,
    SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price, 0)  )                  AS lifetime_revenue,
    SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price - p.cost, 0))           AS lifetime_margin
  FROM
    `bigquery-public-data.thelook_ecommerce.order_items` AS oi
    INNER JOIN `bigquery-public-data.thelook_ecommerce.products` AS p
      ON oi.product_id = p.id
  GROUP BY
    oi.user_id
)

SELECT
  ufc.first_purchase_category,
  COUNT(ufc.user_id)                                                                         AS customers,
  COUNTIF(ul.lifetime_orders >= 2)                                                          AS repeat_buyers,
  ROUND(SAFE_DIVIDE(COUNTIF(ul.lifetime_orders >= 2), COUNT(ufc.user_id)) * 100, 2)         AS repeat_buyer_rate,
  ROUND(SAFE_DIVIDE(SUM(ul.lifetime_orders), COUNT(ufc.user_id)), 2)                        AS avg_lifetime_orders,
  ROUND(SAFE_DIVIDE(SUM(ul.lifetime_revenue), COUNT(ufc.user_id)), 2)                       AS avg_lifetime_revenue,
  ROUND(SAFE_DIVIDE(SUM(ul.lifetime_margin), COUNT(ufc.user_id)), 2)                        AS avg_lifetime_margin,
  ROUND(SAFE_DIVIDE(SUM(ul.lifetime_margin), SUM(ul.lifetime_revenue)) * 100, 2)            AS lifetime_margin_pct

FROM
  user_first_category AS ufc
  INNER JOIN user_lifetime AS ul
    ON ufc.user_id = ul.user_id
GROUP BY
  ufc.first_purchase_category
ORDER BY
  avg_lifetime_margin DESC;


-- =============================================================================
-- 4. HIGH-VALUE FIRST PURCHASE CATEGORIES
-- One row per first-purchase category
-- Extends Query 3 with a value_tier classification:
--   High value — avg_lifetime_margin is above the cross-category average
--   Low value  — avg_lifetime_margin is at or below the cross-category average
-- =============================================================================

WITH ranked_orders AS (
  SELECT
    user_id,
    order_id,
    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at ASC) AS order_rank
  FROM
    `bigquery-public-data.thelook_ecommerce.orders`
),

first_order_ids AS (
  SELECT user_id, order_id
  FROM ranked_orders
  WHERE order_rank = 1
),

first_order_categories AS (
  SELECT
    foi.user_id,
    p.category,
    SUM(oi.sale_price) AS category_revenue_in_first_order
  FROM
    first_order_ids AS foi
    INNER JOIN `bigquery-public-data.thelook_ecommerce.order_items` AS oi
      ON foi.order_id = oi.order_id
    INNER JOIN `bigquery-public-data.thelook_ecommerce.products` AS p
      ON oi.product_id = p.id
  GROUP BY
    foi.user_id, p.category
),

user_first_category AS (
  SELECT user_id, category AS first_purchase_category
  FROM (
    SELECT
      user_id,
      category,
      ROW_NUMBER() OVER (
        PARTITION BY user_id
        ORDER BY category_revenue_in_first_order DESC, category ASC
      ) AS cat_rank
    FROM first_order_categories
  )
  WHERE cat_rank = 1
),

user_lifetime AS (
  SELECT
    oi.user_id,
    COUNT(DISTINCT oi.order_id)                                                              AS lifetime_orders,
    SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price, 0))                    AS lifetime_revenue,
    SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price - p.cost, 0))           AS lifetime_margin
  FROM
    `bigquery-public-data.thelook_ecommerce.order_items` AS oi
    INNER JOIN `bigquery-public-data.thelook_ecommerce.products` AS p
      ON oi.product_id = p.id
  GROUP BY
    oi.user_id
),

category_ltv AS (
  SELECT
    ufc.first_purchase_category,
    COUNT(ufc.user_id)                                                                       AS customers,
    ROUND(SAFE_DIVIDE(COUNTIF(ul.lifetime_orders >= 2), COUNT(ufc.user_id)) * 100, 2)       AS repeat_buyer_rate,
    ROUND(SAFE_DIVIDE(SUM(ul.lifetime_revenue), COUNT(ufc.user_id)), 2)                     AS avg_lifetime_revenue,
    ROUND(SAFE_DIVIDE(SUM(ul.lifetime_margin), COUNT(ufc.user_id)), 2)                      AS avg_lifetime_margin,
    ROUND(SAFE_DIVIDE(SUM(ul.lifetime_margin), SUM(ul.lifetime_revenue)) * 100, 2)          AS lifetime_margin_pct
  FROM
    user_first_category AS ufc
    INNER JOIN user_lifetime AS ul
      ON ufc.user_id = ul.user_id
  GROUP BY
    ufc.first_purchase_category
),

overall_avg AS (
  SELECT AVG(avg_lifetime_margin) AS overall_avg_lifetime_margin
  FROM category_ltv
)

SELECT
  cl.first_purchase_category,
  cl.customers,
  cl.avg_lifetime_margin,
  cl.avg_lifetime_revenue,
  cl.repeat_buyer_rate,
  cl.lifetime_margin_pct,
  CASE
    WHEN cl.avg_lifetime_margin > oa.overall_avg_lifetime_margin THEN 'High value'
    ELSE 'Low value'
  END AS value_tier

FROM
  category_ltv AS cl
  CROSS JOIN overall_avg AS oa
ORDER BY
  cl.avg_lifetime_margin DESC;


-- =============================================================================
-- 5. PRODUCT CATEGORY RECOMMENDATION TABLE
-- One row per product category
-- Combines category-level business metrics with first-purchase LTV signal
--
-- Strategic roles are assigned by comparing each category against the
-- cross-category averages for net_revenue, estimated_net_margin_pct, and
-- avg_lifetime_margin_if_first_purchase. Categories with no first-purchase LTV
-- data are treated as 0 for the LTV comparison only.
--
-- Role assignment (mutually exclusive, evaluated top to bottom):
--   Revenue leader           — above-average revenue AND above-average margin
--   Low-margin volume cat.   — above-average revenue AND below-average margin
--   Margin leader            — below-average revenue AND above-average margin
--   High-value acquisition   — below-average revenue, below-average margin,
--                              but above-average first-purchase LTV signal
--   Niche category           — below average on all three dimensions
-- =============================================================================

WITH category_metrics AS (
  SELECT
    p.category,
    ROUND(SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price, 0)), 2)          AS net_revenue,
    ROUND(
      SAFE_DIVIDE(
        SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price - p.cost, 0)),
        SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price, 0))
      ) * 100,
      2
    )                                                                                         AS estimated_net_margin_pct
  FROM
    `bigquery-public-data.thelook_ecommerce.order_items` AS oi
    INNER JOIN `bigquery-public-data.thelook_ecommerce.products` AS p
      ON oi.product_id = p.id
  GROUP BY
    p.category
),

ranked_orders AS (
  SELECT
    user_id,
    order_id,
    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at ASC) AS order_rank
  FROM
    `bigquery-public-data.thelook_ecommerce.orders`
),

first_order_ids AS (
  SELECT user_id, order_id
  FROM ranked_orders
  WHERE order_rank = 1
),

first_order_categories AS (
  SELECT
    foi.user_id,
    p.category,
    SUM(oi.sale_price) AS category_revenue_in_first_order
  FROM
    first_order_ids AS foi
    INNER JOIN `bigquery-public-data.thelook_ecommerce.order_items` AS oi
      ON foi.order_id = oi.order_id
    INNER JOIN `bigquery-public-data.thelook_ecommerce.products` AS p
      ON oi.product_id = p.id
  GROUP BY
    foi.user_id, p.category
),

user_first_category AS (
  SELECT user_id, category AS first_purchase_category
  FROM (
    SELECT
      user_id,
      category,
      ROW_NUMBER() OVER (
        PARTITION BY user_id
        ORDER BY category_revenue_in_first_order DESC, category ASC
      ) AS cat_rank
    FROM first_order_categories
  )
  WHERE cat_rank = 1
),

user_lifetime AS (
  SELECT
    oi.user_id,
    SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price - p.cost, 0))           AS lifetime_margin
  FROM
    `bigquery-public-data.thelook_ecommerce.order_items` AS oi
    INNER JOIN `bigquery-public-data.thelook_ecommerce.products` AS p
      ON oi.product_id = p.id
  GROUP BY
    oi.user_id
),

category_ltv_summary AS (
  -- Average lifetime margin per first-purchase category
  SELECT
    ufc.first_purchase_category                                                              AS category,
    ROUND(SAFE_DIVIDE(SUM(ul.lifetime_margin), COUNT(ufc.user_id)), 2)                      AS avg_lifetime_margin_if_first_purchase
  FROM
    user_first_category AS ufc
    INNER JOIN user_lifetime AS ul
      ON ufc.user_id = ul.user_id
  GROUP BY
    ufc.first_purchase_category
),

combined AS (
  -- Join metrics and LTV; compute cross-category averages as window scalars
  SELECT
    cm.category,
    cm.net_revenue,
    cm.estimated_net_margin_pct,
    cl.avg_lifetime_margin_if_first_purchase,

    -- Cross-category averages used in role assignment below
    AVG(cm.net_revenue)              OVER ()                                                 AS avg_net_revenue,
    AVG(cm.estimated_net_margin_pct) OVER ()                                                 AS avg_margin_pct,
    -- AVG ignores NULLs, so categories with no LTV data do not distort the average
    AVG(cl.avg_lifetime_margin_if_first_purchase) OVER ()                                    AS avg_ltv_margin

  FROM
    category_metrics AS cm
    LEFT JOIN category_ltv_summary AS cl
      ON cm.category = cl.category
),

with_roles AS (
  SELECT
    category,
    net_revenue,
    estimated_net_margin_pct,
    avg_lifetime_margin_if_first_purchase,
    CASE
      WHEN net_revenue >= avg_net_revenue AND estimated_net_margin_pct >= avg_margin_pct
        THEN 'Revenue leader'
      WHEN net_revenue >= avg_net_revenue AND estimated_net_margin_pct < avg_margin_pct
        THEN 'Low-margin volume category'
      WHEN net_revenue < avg_net_revenue AND estimated_net_margin_pct >= avg_margin_pct
        THEN 'Margin leader'
      WHEN net_revenue < avg_net_revenue
        AND COALESCE(avg_lifetime_margin_if_first_purchase, 0) >= avg_ltv_margin
        THEN 'High-value acquisition category'
      ELSE 'Niche category'
    END AS strategic_role
  FROM combined
)

SELECT
  category,
  strategic_role,
  net_revenue,
  estimated_net_margin_pct,
  avg_lifetime_margin_if_first_purchase,
  CASE strategic_role
    WHEN 'Revenue leader'
      THEN 'Core business driver; protect availability and marketing investment'
    WHEN 'Low-margin volume category'
      THEN 'High volume but margin drag; review pricing or cost structure'
    WHEN 'Margin leader'
      THEN 'High-efficiency category; consider scaling to improve overall margin mix'
    WHEN 'High-value acquisition category'
      THEN 'Strong LTV signal; consider prioritizing for new-user acquisition'
    ELSE
      'Limited scale or differentiation; monitor but do not over-invest'
  END AS recommendation_note

FROM with_roles
ORDER BY net_revenue DESC;
