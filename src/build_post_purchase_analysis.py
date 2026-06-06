"""
build_post_purchase_analysis.py

Runs post-purchase loss analysis against data/processed/ using DuckDB.
Writes five output CSVs to outputs/tables/.
Run from the repo root: python src/build_post_purchase_analysis.py

Status values in order_items: Complete, Processing, Shipped, Returned, Cancelled
Gross revenue  = SUM(sale_price) for all items regardless of status
Net revenue    = gross minus cancelled and returned
Margin impact  = (sale_price - cost) for cancelled + returned items (lost margin)
"""

from pathlib import Path
import csv
import duckdb

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REPO_ROOT   = Path(__file__).parent.parent
DATA_DIR    = REPO_ROOT / "data" / "processed"
OUTPUT_DIR  = REPO_ROOT / "outputs" / "tables"

ORDERS       = str(DATA_DIR / "orders.csv").replace("\\", "/")
ORDER_ITEMS  = str(DATA_DIR / "order_items.csv").replace("\\", "/")
PRODUCTS     = str(DATA_DIR / "products.csv").replace("\\", "/")
INV_ITEMS    = str(DATA_DIR / "inventory_items.csv").replace("\\", "/")
DIST_CENTERS = str(DATA_DIR / "distribution_centers.csv").replace("\\", "/")


# ---------------------------------------------------------------------------
# SQL
# ---------------------------------------------------------------------------

# Q1 — Overall post-purchase loss summary.
# Single aggregate row across all order items.
# Baseline for the full analysis: how much revenue and margin is lost to
# cancellations and returns in total.
SQL_POST_PURCHASE_SUMMARY = """
SELECT
    COUNT(oi.id)                                                                        AS total_items,
    COUNT(DISTINCT oi.order_id)                                                         AS total_orders,
    ROUND(SUM(oi.sale_price), 2)                                                        AS gross_revenue,
    ROUND(SUM(CASE WHEN oi.status = 'Cancelled' THEN oi.sale_price ELSE 0 END), 2)     AS cancelled_revenue,
    ROUND(SUM(CASE WHEN oi.status = 'Returned'  THEN oi.sale_price ELSE 0 END), 2)     AS returned_revenue,
    ROUND(SUM(CASE WHEN oi.status NOT IN ('Cancelled','Returned')
                   THEN oi.sale_price ELSE 0 END), 2)                                  AS net_revenue,
    ROUND(100.0 * COUNT(*) FILTER (WHERE oi.status = 'Cancelled')
          / NULLIF(COUNT(*), 0), 2)                                                     AS cancellation_rate,
    ROUND(100.0 * COUNT(*) FILTER (WHERE oi.status = 'Returned')
          / NULLIF(COUNT(*), 0), 2)                                                     AS return_rate,
    ROUND(SUM(CASE WHEN oi.status IN ('Cancelled','Returned')
                   THEN oi.sale_price - p.cost ELSE 0 END), 2)                         AS estimated_margin_impact
FROM order_items oi
JOIN products p ON oi.product_id = p.id
"""


# Q2 — Post-purchase loss by product category.
# One row per category. Identifies which categories drive the most cancellation
# and return revenue loss. Ordered by gross_revenue desc to show largest
# categories first and let relative rates be compared in context.
SQL_POST_PURCHASE_BY_CATEGORY = """
SELECT
    p.category,
    COUNT(oi.id)                                                                        AS total_items,
    ROUND(SUM(oi.sale_price), 2)                                                        AS gross_revenue,
    ROUND(SUM(CASE WHEN oi.status = 'Cancelled' THEN oi.sale_price ELSE 0 END), 2)     AS cancelled_revenue,
    ROUND(SUM(CASE WHEN oi.status = 'Returned'  THEN oi.sale_price ELSE 0 END), 2)     AS returned_revenue,
    ROUND(SUM(CASE WHEN oi.status NOT IN ('Cancelled','Returned')
                   THEN oi.sale_price ELSE 0 END), 2)                                  AS net_revenue,
    ROUND(100.0 * COUNT(*) FILTER (WHERE oi.status = 'Cancelled')
          / NULLIF(COUNT(*), 0), 2)                                                     AS cancellation_rate,
    ROUND(100.0 * COUNT(*) FILTER (WHERE oi.status = 'Returned')
          / NULLIF(COUNT(*), 0), 2)                                                     AS return_rate,
    ROUND(SUM(CASE WHEN oi.status IN ('Cancelled','Returned')
                   THEN oi.sale_price - p.cost ELSE 0 END), 2)                         AS estimated_margin_impact
FROM order_items oi
JOIN products p ON oi.product_id = p.id
GROUP BY p.category
ORDER BY gross_revenue DESC
"""


# Q3 — Post-purchase loss by order value band.
# Buckets orders by their total gross value (all items, all statuses).
# Rates are computed at the item level within each band.
# Answers: do high-value or low-value orders cancel / return more?
SQL_POST_PURCHASE_BY_ORDER_VALUE = """
WITH order_totals AS (
    SELECT
        order_id,
        SUM(sale_price)                                             AS order_gross_value,
        COUNT(*)                                                    AS items,
        COUNT(*) FILTER (WHERE status = 'Cancelled')               AS cancelled_items,
        COUNT(*) FILTER (WHERE status = 'Returned')                AS returned_items,
        SUM(CASE WHEN status = 'Cancelled' THEN sale_price ELSE 0 END) AS cancelled_revenue,
        SUM(CASE WHEN status = 'Returned'  THEN sale_price ELSE 0 END) AS returned_revenue,
        SUM(CASE WHEN status NOT IN ('Cancelled','Returned')
                 THEN sale_price ELSE 0 END)                       AS net_revenue
    FROM order_items
    GROUP BY order_id
),
bucketed AS (
    SELECT
        CASE
            WHEN order_gross_value <  50  THEN '< $50'
            WHEN order_gross_value < 100  THEN '$50 – $99'
            WHEN order_gross_value < 200  THEN '$100 – $199'
            ELSE '$200+'
        END AS order_value_band,
        CASE
            WHEN order_gross_value <  50  THEN 1
            WHEN order_gross_value < 100  THEN 2
            WHEN order_gross_value < 200  THEN 3
            ELSE 4
        END AS band_sort,
        items, cancelled_items, returned_items,
        order_gross_value, cancelled_revenue, returned_revenue, net_revenue
    FROM order_totals
)
SELECT
    order_value_band,
    COUNT(*)                                                        AS orders,
    SUM(items)                                                      AS total_items,
    ROUND(SUM(order_gross_value), 2)                                AS gross_revenue,
    ROUND(SUM(cancelled_revenue), 2)                                AS cancelled_revenue,
    ROUND(SUM(returned_revenue), 2)                                 AS returned_revenue,
    ROUND(SUM(net_revenue), 2)                                      AS net_revenue,
    ROUND(100.0 * SUM(cancelled_items) / NULLIF(SUM(items), 0), 2) AS cancellation_rate,
    ROUND(100.0 * SUM(returned_items)  / NULLIF(SUM(items), 0), 2) AS return_rate,
    ROUND(SUM(order_gross_value) / NULLIF(COUNT(*), 0), 2)         AS avg_order_value
FROM bucketed
GROUP BY order_value_band, band_sort
ORDER BY band_sort
"""


# Q4 — Post-purchase loss by customer type (new vs repeat).
# New = item belongs to the user's first order (by orders.created_at, then order_id).
# Repeat = all items from subsequent orders.
# Answers: do new customers or repeat customers cancel / return more?
SQL_POST_PURCHASE_BY_CUSTOMER_TYPE = """
WITH ranked_orders AS (
    SELECT
        user_id,
        order_id,
        ROW_NUMBER() OVER (
            PARTITION BY user_id
            ORDER BY created_at ASC, order_id ASC
        ) AS order_rank
    FROM orders
),
order_type AS (
    SELECT
        order_id,
        CASE WHEN order_rank = 1
             THEN 'New customer (first order)'
             ELSE 'Repeat customer (post-first)'
        END AS customer_type
    FROM ranked_orders
)
SELECT
    ot.customer_type,
    COUNT(oi.id)                                                                        AS total_items,
    COUNT(DISTINCT oi.order_id)                                                         AS orders,
    ROUND(SUM(oi.sale_price), 2)                                                        AS gross_revenue,
    ROUND(SUM(CASE WHEN oi.status = 'Cancelled' THEN oi.sale_price ELSE 0 END), 2)     AS cancelled_revenue,
    ROUND(SUM(CASE WHEN oi.status = 'Returned'  THEN oi.sale_price ELSE 0 END), 2)     AS returned_revenue,
    ROUND(SUM(CASE WHEN oi.status NOT IN ('Cancelled','Returned')
                   THEN oi.sale_price ELSE 0 END), 2)                                  AS net_revenue,
    ROUND(100.0 * COUNT(*) FILTER (WHERE oi.status = 'Cancelled')
          / NULLIF(COUNT(*), 0), 2)                                                     AS cancellation_rate,
    ROUND(100.0 * COUNT(*) FILTER (WHERE oi.status = 'Returned')
          / NULLIF(COUNT(*), 0), 2)                                                     AS return_rate,
    ROUND(SUM(CASE WHEN oi.status IN ('Cancelled','Returned')
                   THEN oi.sale_price - p.cost ELSE 0 END), 2)                         AS estimated_margin_impact
FROM order_items oi
JOIN products p ON oi.product_id = p.id
JOIN order_type ot ON oi.order_id = ot.order_id
GROUP BY ot.customer_type
ORDER BY ot.customer_type
"""


# Q5 — Post-purchase loss and delivery timing by distribution center.
# Joins order_items → inventory_items → distribution_centers via inventory_item_id.
# Items without a matching inventory record are excluded (no DC assignment possible).
# avg_days_to_ship  = order_items.created_at → shipped_at  (fulfillment speed)
# avg_days_to_deliver = shipped_at → delivered_at           (carrier transit time)
# Answers: which DCs have the worst loss rates or slowest delivery performance?
SQL_POST_PURCHASE_BY_DISTRIBUTION_CENTER = """
WITH item_dc AS (
    SELECT
        oi.id                   AS item_id,
        oi.status,
        oi.sale_price,
        p.cost,
        oi.created_at           AS item_created_at,
        oi.shipped_at,
        oi.delivered_at,
        dc.name                 AS distribution_center
    FROM order_items oi
    JOIN products p          ON oi.product_id          = p.id
    JOIN inventory_items ii  ON oi.inventory_item_id   = ii.id
    JOIN distribution_centers dc ON ii.product_distribution_center_id = dc.id
)
SELECT
    distribution_center,
    COUNT(*)                                                                            AS total_items,
    ROUND(SUM(sale_price), 2)                                                           AS gross_revenue,
    ROUND(SUM(CASE WHEN status = 'Cancelled' THEN sale_price ELSE 0 END), 2)           AS cancelled_revenue,
    ROUND(SUM(CASE WHEN status = 'Returned'  THEN sale_price ELSE 0 END), 2)           AS returned_revenue,
    ROUND(SUM(CASE WHEN status NOT IN ('Cancelled','Returned')
                   THEN sale_price ELSE 0 END), 2)                                     AS net_revenue,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'Cancelled')
          / NULLIF(COUNT(*), 0), 2)                                                     AS cancellation_rate,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'Returned')
          / NULLIF(COUNT(*), 0), 2)                                                     AS return_rate,
    ROUND(SUM(CASE WHEN status IN ('Cancelled','Returned')
                   THEN sale_price - cost ELSE 0 END), 2)                              AS estimated_margin_impact,
    ROUND(AVG(CASE WHEN shipped_at   IS NOT NULL AND item_created_at IS NOT NULL
                   THEN date_diff('day', item_created_at::DATE, shipped_at::DATE)
              END), 1)                                                                  AS avg_days_to_ship,
    ROUND(AVG(CASE WHEN delivered_at IS NOT NULL AND shipped_at IS NOT NULL
                   THEN date_diff('day', shipped_at::DATE, delivered_at::DATE)
              END), 1)                                                                  AS avg_days_to_deliver
FROM item_dc
GROUP BY distribution_center
ORDER BY gross_revenue DESC
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def register_views(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(f"CREATE OR REPLACE VIEW orders             AS SELECT * FROM read_csv_auto('{ORDERS}')")
    con.execute(f"CREATE OR REPLACE VIEW order_items        AS SELECT * FROM read_csv_auto('{ORDER_ITEMS}')")
    con.execute(f"CREATE OR REPLACE VIEW products           AS SELECT * FROM read_csv_auto('{PRODUCTS}')")
    con.execute(f"CREATE OR REPLACE VIEW inventory_items    AS SELECT * FROM read_csv_auto('{INV_ITEMS}')")
    con.execute(f"CREATE OR REPLACE VIEW distribution_centers AS SELECT * FROM read_csv_auto('{DIST_CENTERS}')")


def run_query(
    con: duckdb.DuckDBPyConnection,
    sql: str,
    output_path: Path,
    label: str,
) -> int:
    print(f"  {label} ...", end=" ", flush=True)
    result = con.execute(sql)
    cols   = [d[0] for d in result.description]
    rows   = result.fetchall()
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(cols)
        writer.writerows(rows)
    print(f"{len(rows)} rows  ->  {output_path.name}")
    return len(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

QUERIES = [
    (SQL_POST_PURCHASE_SUMMARY,
     "post_purchase_summary.csv",
     "Overall post-purchase summary"),

    (SQL_POST_PURCHASE_BY_CATEGORY,
     "post_purchase_by_category.csv",
     "Post-purchase loss by category"),

    (SQL_POST_PURCHASE_BY_ORDER_VALUE,
     "post_purchase_by_order_value.csv",
     "Post-purchase loss by order value band"),

    (SQL_POST_PURCHASE_BY_CUSTOMER_TYPE,
     "post_purchase_by_customer_type.csv",
     "Post-purchase loss by customer type"),

    (SQL_POST_PURCHASE_BY_DISTRIBUTION_CENTER,
     "post_purchase_by_distribution_center.csv",
     "Post-purchase loss by distribution center"),
]


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\nE-Commerce Growth Analytics - Post-Purchase Loss Analysis")
    print(f"Source:  {DATA_DIR}")
    print(f"Output:  {OUTPUT_DIR}")
    print(f"\nRunning {len(QUERIES)} queries:\n")

    con = duckdb.connect()
    register_views(con)

    total_rows = 0
    for sql, filename, label in QUERIES:
        n = run_query(con, sql, OUTPUT_DIR / filename, label)
        total_rows += n

    con.close()
    print(f"\nDone. {len(QUERIES)} files written, {total_rows:,} total rows.")


if __name__ == "__main__":
    main()
