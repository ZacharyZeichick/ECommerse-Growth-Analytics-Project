-- =============================================================================
-- Phase 1: Schema Discovery — theLook eCommerce
-- Dataset: bigquery-public-data.thelook_ecommerce
-- Purpose: Confirm table availability, row counts, column schemas,
--          date ranges, and sample rows for all key tables.
-- =============================================================================


-- =============================================================================
-- SECTION 1: List available tables in the dataset
-- =============================================================================

-- Lists all tables in thelook_ecommerce with name, type, and creation time.
SELECT
  table_name,
  table_type,
  creation_time
FROM `bigquery-public-data.thelook_ecommerce.INFORMATION_SCHEMA.TABLES`
ORDER BY table_name
;

-- Simpler list of table names only.
SELECT
  table_name,
  table_type
FROM `bigquery-public-data.thelook_ecommerce.INFORMATION_SCHEMA.TABLES`
ORDER BY table_name
;


-- =============================================================================
-- SECTION 2: Row counts for each key table
-- =============================================================================

-- Row count: orders
SELECT COUNT(*) AS row_count, 'orders' AS table_name
FROM `bigquery-public-data.thelook_ecommerce.orders`
;

-- Row count: order_items
SELECT COUNT(*) AS row_count, 'order_items' AS table_name
FROM `bigquery-public-data.thelook_ecommerce.order_items`
;

-- Row count: users
SELECT COUNT(*) AS row_count, 'users' AS table_name
FROM `bigquery-public-data.thelook_ecommerce.users`
;

-- Row count: products
SELECT COUNT(*) AS row_count, 'products' AS table_name
FROM `bigquery-public-data.thelook_ecommerce.products`
;

-- Row count: inventory_items
SELECT COUNT(*) AS row_count, 'inventory_items' AS table_name
FROM `bigquery-public-data.thelook_ecommerce.inventory_items`
;

-- Row count: events
SELECT COUNT(*) AS row_count, 'events' AS table_name
FROM `bigquery-public-data.thelook_ecommerce.events`
;

-- Row count: distribution_centers
SELECT COUNT(*) AS row_count, 'distribution_centers' AS table_name
FROM `bigquery-public-data.thelook_ecommerce.distribution_centers`
;


-- =============================================================================
-- SECTION 3: Column names and data types for each key table
-- =============================================================================

-- Column schema: orders
SELECT
  column_name,
  data_type,
  is_nullable
FROM `bigquery-public-data.thelook_ecommerce.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'orders'
ORDER BY ordinal_position
;

-- Column schema: order_items
SELECT
  column_name,
  data_type,
  is_nullable
FROM `bigquery-public-data.thelook_ecommerce.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'order_items'
ORDER BY ordinal_position
;

-- Column schema: users
SELECT
  column_name,
  data_type,
  is_nullable
FROM `bigquery-public-data.thelook_ecommerce.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'users'
ORDER BY ordinal_position
;

-- Column schema: products
SELECT
  column_name,
  data_type,
  is_nullable
FROM `bigquery-public-data.thelook_ecommerce.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'products'
ORDER BY ordinal_position
;

-- Column schema: inventory_items
SELECT
  column_name,
  data_type,
  is_nullable
FROM `bigquery-public-data.thelook_ecommerce.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'inventory_items'
ORDER BY ordinal_position
;

-- Column schema: events
SELECT
  column_name,
  data_type,
  is_nullable
FROM `bigquery-public-data.thelook_ecommerce.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'events'
ORDER BY ordinal_position
;

-- Column schema: distribution_centers
SELECT
  column_name,
  data_type,
  is_nullable
FROM `bigquery-public-data.thelook_ecommerce.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'distribution_centers'
ORDER BY ordinal_position
;


-- =============================================================================
-- SECTION 4: Date ranges for timestamp/date fields
-- =============================================================================

-- Date range: orders (created_at, shipped_at, delivered_at, returned_at)
SELECT
  MIN(created_at)   AS orders_created_min,
  MAX(created_at)   AS orders_created_max,
  MIN(shipped_at)   AS orders_shipped_min,
  MAX(shipped_at)   AS orders_shipped_max,
  MIN(delivered_at) AS orders_delivered_min,
  MAX(delivered_at) AS orders_delivered_max,
  MIN(returned_at)  AS orders_returned_min,
  MAX(returned_at)  AS orders_returned_max
FROM `bigquery-public-data.thelook_ecommerce.orders`
;

-- Date range: order_items (created_at, shipped_at, delivered_at, returned_at)
SELECT
  MIN(created_at)   AS items_created_min,
  MAX(created_at)   AS items_created_max,
  MIN(shipped_at)   AS items_shipped_min,
  MAX(shipped_at)   AS items_shipped_max,
  MIN(delivered_at) AS items_delivered_min,
  MAX(delivered_at) AS items_delivered_max,
  MIN(returned_at)  AS items_returned_min,
  MAX(returned_at)  AS items_returned_max
FROM `bigquery-public-data.thelook_ecommerce.order_items`
;

-- Date range: users (created_at)
SELECT
  MIN(created_at) AS users_created_min,
  MAX(created_at) AS users_created_max
FROM `bigquery-public-data.thelook_ecommerce.users`
;

-- Date range: events (created_at)
SELECT
  MIN(created_at) AS events_created_min,
  MAX(created_at) AS events_created_max
FROM `bigquery-public-data.thelook_ecommerce.events`
;

-- Date range: inventory_items (created_at, sold_at)
SELECT
  MIN(created_at) AS inventory_created_min,
  MAX(created_at) AS inventory_created_max,
  MIN(sold_at)    AS inventory_sold_min,
  MAX(sold_at)    AS inventory_sold_max
FROM `bigquery-public-data.thelook_ecommerce.inventory_items`
;


-- =============================================================================
-- SECTION 5: Sample rows (LIMIT 10) for each key table
-- =============================================================================

-- Sample: orders
SELECT *
FROM `bigquery-public-data.thelook_ecommerce.orders`
LIMIT 10
;

-- Sample: order_items
SELECT *
FROM `bigquery-public-data.thelook_ecommerce.order_items`
LIMIT 10
;

-- Sample: users
SELECT *
FROM `bigquery-public-data.thelook_ecommerce.users`
LIMIT 10
;

-- Sample: products
SELECT *
FROM `bigquery-public-data.thelook_ecommerce.products`
LIMIT 10
;

-- Sample: inventory_items
SELECT *
FROM `bigquery-public-data.thelook_ecommerce.inventory_items`
LIMIT 10
;

-- Sample: events
SELECT *
FROM `bigquery-public-data.thelook_ecommerce.events`
LIMIT 10
;

-- Sample: distribution_centers
SELECT *
FROM `bigquery-public-data.thelook_ecommerce.distribution_centers`
LIMIT 10
;
