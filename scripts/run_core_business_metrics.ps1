# =============================================================================
# run_core_business_metrics.ps1
# Exports the five core business metric queries from
# sql/02_core_business_metrics.sql via the bq CLI.
#
# Prerequisites:
#   - Google Cloud SDK installed and on PATH
#   - Authenticated: gcloud auth login
#   - Billing project configured: gcloud config set project YOUR_PROJECT_ID
#   - Run from the repo root directory
#
# Outputs written to outputs/tables/:
#   overall_business_summary.csv
#   monthly_business_metrics.csv
#   category_business_metrics.csv
#   customer_purchase_summary.csv
#   order_status_rates.csv
# =============================================================================

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$OutputDir = "outputs\tables"

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
    Write-Host "Created output directory: $OutputDir"
}

# Runs a BigQuery Standard SQL query via the bq CLI and saves the result as CSV.
# Writes the query to a temp file to avoid PowerShell escaping issues with
# BigQuery backtick syntax, then pipes the file content into bq via stdin.
# stdout (CSV rows) and stderr (bq diagnostics) are kept separate.
function Invoke-BqQuery {
    param(
        [string]$QueryText,
        [string]$OutputPath,
        [string]$Label
    )
    Write-Host "Running: $Label..."
    $tmpSql = [System.IO.Path]::GetTempFileName()
    $tmpErr = [System.IO.Path]::GetTempFileName()
    try {
        Set-Content -Path $tmpSql -Value $QueryText -Encoding UTF8
        $output = Get-Content $tmpSql | bq --quiet query --use_legacy_sql=false --format=csv --max_rows=10000 2>$tmpErr
        if ($LASTEXITCODE -ne 0) {
            $errText = Get-Content $tmpErr -Raw -ErrorAction SilentlyContinue
            Write-Host "bq error output: $errText"
            throw "bq query failed for: $Label"
        }
        Set-Content -Path $OutputPath -Value $output -Encoding UTF8
        Write-Host "  Saved: $OutputPath"
    }
    finally {
        Remove-Item $tmpSql -ErrorAction SilentlyContinue
        Remove-Item $tmpErr -ErrorAction SilentlyContinue
    }
}


# =============================================================================
# 1. OVERALL BUSINESS SUMMARY
# Single-row summary: orders, buyers, revenue, cost, margin, and AOV
# Gross = all statuses; Net = excludes Cancelled and Returned
# =============================================================================

$q1 = @'
SELECT
  COUNT(DISTINCT oi.order_id)                                                             AS total_orders,
  COUNT(DISTINCT oi.user_id)                                                              AS total_buyers,
  COUNT(oi.id)                                                                            AS total_items,
  ROUND(SUM(oi.sale_price), 2)                                                            AS gross_revenue,
  ROUND(SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price, 0)), 2)         AS net_revenue,
  ROUND(SUM(p.cost), 2)                                                                   AS estimated_gross_cost,
  ROUND(SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), p.cost, 0)), 2)                AS estimated_net_cost,
  ROUND(SUM(oi.sale_price) - SUM(p.cost), 2)                                              AS estimated_gross_margin,
  ROUND(
    SAFE_DIVIDE(SUM(oi.sale_price) - SUM(p.cost), SUM(oi.sale_price)) * 100,
    2
  )                                                                                        AS estimated_gross_margin_pct,
  ROUND(SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price - p.cost, 0)), 2) AS estimated_net_margin,
  ROUND(
    SAFE_DIVIDE(
      SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price - p.cost, 0)),
      SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price, 0))
    ) * 100,
    2
  )                                                                                        AS estimated_net_margin_pct,
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
    ON oi.product_id = p.id
'@

Invoke-BqQuery -QueryText $q1 -OutputPath "$OutputDir\overall_business_summary.csv" -Label "Overall Business Summary"


# =============================================================================
# 2. MONTHLY BUSINESS METRICS
# One row per calendar month (YYYY-MM): revenue, margin, and AOV over time
# =============================================================================

$q2 = @'
SELECT
  FORMAT_DATE('%Y-%m', DATE(oi.created_at))                                                AS order_month,
  COUNT(DISTINCT oi.order_id)                                                              AS orders,
  COUNT(DISTINCT oi.user_id)                                                               AS buyers,
  COUNT(oi.id)                                                                             AS items_sold,
  ROUND(SUM(oi.sale_price), 2)                                                             AS gross_revenue,
  ROUND(SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price, 0)), 2)          AS net_revenue,
  ROUND(SUM(oi.sale_price) - SUM(p.cost), 2)                                               AS estimated_gross_margin,
  ROUND(
    SAFE_DIVIDE(SUM(oi.sale_price) - SUM(p.cost), SUM(oi.sale_price)) * 100,
    2
  )                                                                                         AS estimated_gross_margin_pct,
  ROUND(SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price - p.cost, 0)), 2) AS estimated_net_margin,
  ROUND(
    SAFE_DIVIDE(
      SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price - p.cost, 0)),
      SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price, 0))
    ) * 100,
    2
  )                                                                                         AS estimated_net_margin_pct,
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
  order_month
'@

Invoke-BqQuery -QueryText $q2 -OutputPath "$OutputDir\monthly_business_metrics.csv" -Label "Monthly Business Metrics"


# =============================================================================
# 3. CATEGORY BUSINESS METRICS
# One row per product category: revenue, margin, avg item price, return and cancel rates
# =============================================================================

$q3 = @'
SELECT
  p.category,
  COUNT(oi.id)                                                                             AS items_sold,
  COUNT(DISTINCT oi.order_id)                                                              AS orders,
  COUNT(DISTINCT oi.user_id)                                                               AS buyers,
  ROUND(SUM(oi.sale_price), 2)                                                             AS gross_revenue,
  ROUND(SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price, 0)), 2)          AS net_revenue,
  ROUND(SUM(oi.sale_price) - SUM(p.cost), 2)                                               AS estimated_gross_margin,
  ROUND(
    SAFE_DIVIDE(SUM(oi.sale_price) - SUM(p.cost), SUM(oi.sale_price)) * 100,
    2
  )                                                                                         AS estimated_gross_margin_pct,
  ROUND(SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price - p.cost, 0)), 2) AS estimated_net_margin,
  ROUND(
    SAFE_DIVIDE(
      SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price - p.cost, 0)),
      SUM(IF(oi.status NOT IN ('Cancelled', 'Returned'), oi.sale_price, 0))
    ) * 100,
    2
  )                                                                                         AS estimated_net_margin_pct,
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
  gross_revenue DESC
'@

Invoke-BqQuery -QueryText $q3 -OutputPath "$OutputDir\category_business_metrics.csv" -Label "Category Business Metrics"


# =============================================================================
# 4. CUSTOMER PURCHASE SUMMARY
# Single-row summary: one-time vs. repeat buyer counts and rates
# =============================================================================

$q4 = @'
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
  buyer_order_counts
'@

Invoke-BqQuery -QueryText $q4 -OutputPath "$OutputDir\customer_purchase_summary.csv" -Label "Customer Purchase Summary"


# =============================================================================
# 5. ORDER STATUS RATES
# One row per order status: count and share of total orders
# =============================================================================

$q5 = @'
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
  orders DESC
'@

Invoke-BqQuery -QueryText $q5 -OutputPath "$OutputDir\order_status_rates.csv" -Label "Order Status Rates"


Write-Host "`nAll queries complete. Outputs saved to $OutputDir\"
