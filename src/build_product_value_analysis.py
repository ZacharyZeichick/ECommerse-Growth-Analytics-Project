"""
build_product_value_analysis.py

Runs product and customer value analysis against data/processed/ using DuckDB.
Writes five output CSVs to outputs/tables/.
Run from the repo root: python src/build_product_value_analysis.py
"""

from pathlib import Path
import csv
import duckdb

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_DIR   = Path("data/processed")
OUTPUT_DIR = Path("outputs/tables")

ORDERS      = str(DATA_DIR / "orders.csv").replace("\\", "/")
ORDER_ITEMS = str(DATA_DIR / "order_items.csv").replace("\\", "/")
PRODUCTS    = str(DATA_DIR / "products.csv").replace("\\", "/")


# ---------------------------------------------------------------------------
# SQL
# ---------------------------------------------------------------------------

# Q1 — Category revenue and margin ranking.
# One row per product category. Gross includes all statuses; net excludes
# Cancelled and Returned. Ordered by net_revenue desc.
SQL_CATEGORY_VALUE_RANKING = """
SELECT
    p.category,
    COUNT(oi.id)                                                                 AS items_sold,
    COUNT(DISTINCT oi.order_id)                                                  AS orders,
    COUNT(DISTINCT oi.user_id)                                                   AS buyers,
    ROUND(SUM(oi.sale_price), 2)                                                 AS gross_revenue,
    ROUND(SUM(CASE WHEN oi.status NOT IN ('Cancelled','Returned')
                   THEN oi.sale_price ELSE 0 END), 2)                            AS net_revenue,
    ROUND(SUM(CASE WHEN oi.status NOT IN ('Cancelled','Returned')
                   THEN oi.sale_price - p.cost ELSE 0 END), 2)                   AS estimated_net_margin,
    ROUND(
        100.0
        * SUM(CASE WHEN oi.status NOT IN ('Cancelled','Returned')
                   THEN oi.sale_price - p.cost ELSE 0 END)
        / NULLIF(SUM(CASE WHEN oi.status NOT IN ('Cancelled','Returned')
                          THEN oi.sale_price ELSE 0 END), 0.0),
        2
    )                                                                            AS estimated_net_margin_pct,
    ROUND(SUM(oi.sale_price) / NULLIF(COUNT(oi.id), 0), 2)                     AS avg_item_price,
    ROUND(100.0 * COUNT(*) FILTER (WHERE oi.status = 'Returned')
          / NULLIF(COUNT(*), 0), 2)                                              AS return_rate,
    ROUND(100.0 * COUNT(*) FILTER (WHERE oi.status = 'Cancelled')
          / NULLIF(COUNT(*), 0), 2)                                              AS cancellation_rate
FROM order_items oi
JOIN products p ON oi.product_id = p.id
GROUP BY p.category
ORDER BY net_revenue DESC
"""


# Q2 — Revenue vs margin quadrant dataset.
# One row per category. Designed for a scatter plot:
# net_revenue on one axis, estimated_net_margin_pct on the other, buyers as size.
SQL_REVENUE_MARGIN_QUADRANT = """
SELECT
    p.category,
    ROUND(SUM(CASE WHEN oi.status NOT IN ('Cancelled','Returned')
                   THEN oi.sale_price ELSE 0 END), 2)                            AS net_revenue,
    ROUND(
        100.0
        * SUM(CASE WHEN oi.status NOT IN ('Cancelled','Returned')
                   THEN oi.sale_price - p.cost ELSE 0 END)
        / NULLIF(SUM(CASE WHEN oi.status NOT IN ('Cancelled','Returned')
                          THEN oi.sale_price ELSE 0 END), 0.0),
        2
    )                                                                            AS estimated_net_margin_pct,
    COUNT(DISTINCT oi.user_id)                                                   AS buyers,
    COUNT(oi.id)                                                                 AS items_sold,
    ROUND(SUM(oi.sale_price) / NULLIF(COUNT(oi.id), 0), 2)                     AS avg_item_price
FROM order_items oi
JOIN products p ON oi.product_id = p.id
GROUP BY p.category
ORDER BY net_revenue DESC
"""


# Q3 — First-purchase category and lifetime customer value.
# One row per first-purchase category.
# First-purchase category: dominant category (by sale_price) in user's earliest
# order (by orders.created_at); alphabetical tiebreaker on category name.
# Lifetime values aggregate ALL order_items; net excludes Cancelled/Returned.
SQL_FIRST_PURCHASE_CATEGORY_CUSTOMER_VALUE = """
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
    FROM first_order_ids foi
    JOIN order_items oi ON foi.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.id
    GROUP BY foi.user_id, p.category
),
user_first_category AS (
    -- Pick dominant category; category name breaks ties deterministically
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
    ) t
    WHERE cat_rank = 1
),
user_lifetime AS (
    -- Lifetime order count, revenue, and margin per user across all orders
    SELECT
        oi.user_id,
        COUNT(DISTINCT oi.order_id)                                                          AS lifetime_orders,
        SUM(CASE WHEN oi.status NOT IN ('Cancelled','Returned')
                 THEN oi.sale_price ELSE 0 END)                                              AS lifetime_revenue,
        SUM(CASE WHEN oi.status NOT IN ('Cancelled','Returned')
                 THEN oi.sale_price - p.cost ELSE 0 END)                                     AS lifetime_margin
    FROM order_items oi
    JOIN products p ON oi.product_id = p.id
    GROUP BY oi.user_id
)
SELECT
    ufc.first_purchase_category,
    COUNT(ufc.user_id)                                                                       AS customers,
    COUNT(*) FILTER (WHERE ul.lifetime_orders >= 2)                                         AS repeat_buyers,
    ROUND(100.0 * COUNT(*) FILTER (WHERE ul.lifetime_orders >= 2)
          / NULLIF(COUNT(ufc.user_id), 0), 2)                                                AS repeat_buyer_rate,
    ROUND(SUM(ul.lifetime_orders)  / NULLIF(COUNT(ufc.user_id), 0), 2)                     AS avg_lifetime_orders,
    ROUND(SUM(ul.lifetime_revenue) / NULLIF(COUNT(ufc.user_id), 0), 2)                     AS avg_lifetime_revenue,
    ROUND(SUM(ul.lifetime_margin)  / NULLIF(COUNT(ufc.user_id), 0), 2)                     AS avg_lifetime_margin,
    ROUND(100.0 * SUM(ul.lifetime_margin) / NULLIF(SUM(ul.lifetime_revenue), 0), 2)        AS lifetime_margin_pct
FROM user_first_category ufc
JOIN user_lifetime ul ON ufc.user_id = ul.user_id
GROUP BY ufc.first_purchase_category
ORDER BY avg_lifetime_margin DESC
"""


# Q4 — First order vs post-first-order value by first-purchase category.
# One row per first-purchase category.
# Answers whether category LTV is durable after the first order or front-loaded.
# post_first_order_* values are 0 for one-time buyers.
# pct_margin_after_first_order = SUM(post-first margin) / SUM(lifetime margin).
SQL_FIRST_VS_POST_FIRST_ORDER_VALUE = """
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
    FROM first_order_ids foi
    JOIN order_items oi ON foi.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.id
    GROUP BY foi.user_id, p.category
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
    ) t
    WHERE cat_rank = 1
),
first_order_value AS (
    -- Net revenue and margin from each user's first order only
    SELECT
        foi.user_id,
        SUM(CASE WHEN oi.status NOT IN ('Cancelled','Returned')
                 THEN oi.sale_price ELSE 0 END)                                              AS first_order_revenue,
        SUM(CASE WHEN oi.status NOT IN ('Cancelled','Returned')
                 THEN oi.sale_price - p.cost ELSE 0 END)                                     AS first_order_margin
    FROM first_order_ids foi
    JOIN order_items oi ON foi.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.id
    GROUP BY foi.user_id
),
post_first_items AS (
    -- All order items that do NOT belong to the user's first order (anti-join)
    SELECT
        oi.user_id,
        oi.status,
        oi.sale_price,
        p.cost
    FROM order_items oi
    JOIN products p ON oi.product_id = p.id
    LEFT JOIN first_order_ids foi
        ON oi.user_id = foi.user_id AND oi.order_id = foi.order_id
    WHERE foi.order_id IS NULL
),
post_first_order_value AS (
    -- Net revenue and margin from all orders after the first
    SELECT
        user_id,
        SUM(CASE WHEN status NOT IN ('Cancelled','Returned')
                 THEN sale_price ELSE 0 END)                                                 AS post_first_revenue,
        SUM(CASE WHEN status NOT IN ('Cancelled','Returned')
                 THEN sale_price - cost ELSE 0 END)                                          AS post_first_margin
    FROM post_first_items
    GROUP BY user_id
),
user_lifetime AS (
    SELECT
        oi.user_id,
        COUNT(DISTINCT oi.order_id)                                                          AS lifetime_orders,
        SUM(CASE WHEN oi.status NOT IN ('Cancelled','Returned')
                 THEN oi.sale_price ELSE 0 END)                                              AS lifetime_revenue,
        SUM(CASE WHEN oi.status NOT IN ('Cancelled','Returned')
                 THEN oi.sale_price - p.cost ELSE 0 END)                                     AS lifetime_margin
    FROM order_items oi
    JOIN products p ON oi.product_id = p.id
    GROUP BY oi.user_id
)
SELECT
    ufc.first_purchase_category,
    COUNT(ufc.user_id)                                                                       AS customers,
    ROUND(SUM(fov.first_order_revenue)               / NULLIF(COUNT(ufc.user_id), 0), 2)   AS first_order_revenue,
    ROUND(SUM(fov.first_order_margin)                / NULLIF(COUNT(ufc.user_id), 0), 2)   AS first_order_margin,
    ROUND(SUM(COALESCE(pfov.post_first_revenue, 0))  / NULLIF(COUNT(ufc.user_id), 0), 2)   AS post_first_order_revenue,
    ROUND(SUM(COALESCE(pfov.post_first_margin, 0))   / NULLIF(COUNT(ufc.user_id), 0), 2)   AS post_first_order_margin,
    ROUND(SUM(ul.lifetime_revenue)                   / NULLIF(COUNT(ufc.user_id), 0), 2)   AS total_lifetime_revenue,
    ROUND(SUM(ul.lifetime_margin)                    / NULLIF(COUNT(ufc.user_id), 0), 2)   AS total_lifetime_margin,
    ROUND(
        100.0 * SUM(COALESCE(pfov.post_first_margin, 0))
        / NULLIF(SUM(ul.lifetime_margin), 0),
        2
    )                                                                                        AS pct_margin_after_first_order,
    ROUND(100.0 * COUNT(*) FILTER (WHERE ul.lifetime_orders >= 2)
          / NULLIF(COUNT(ufc.user_id), 0), 2)                                                AS repeat_buyer_rate
FROM user_first_category ufc
JOIN  first_order_value      fov  ON ufc.user_id = fov.user_id
LEFT JOIN post_first_order_value pfov ON ufc.user_id = pfov.user_id
JOIN  user_lifetime          ul   ON ufc.user_id = ul.user_id
GROUP BY ufc.first_purchase_category
ORDER BY total_lifetime_margin DESC
"""


# Q5 — Product category recommendations.
# One row per category. Combines Q1 revenue/margin, Q3 LTV signal, and Q4
# post-first-order durability. Strategic role is assigned by comparing each
# category against cross-category averages (evaluated top to bottom):
#   Revenue leader           — above-avg revenue AND above-avg margin
#   Low-margin volume cat.   — above-avg revenue AND below-avg margin
#   Margin leader            — below-avg revenue AND above-avg margin
#   High-value acquisition   — below-avg revenue AND above-avg first-purchase LTV
#   Niche category           — below average on all dimensions
SQL_CATEGORY_RECOMMENDATIONS = """
WITH
category_metrics AS (
    SELECT
        p.category,
        ROUND(SUM(CASE WHEN oi.status NOT IN ('Cancelled','Returned')
                       THEN oi.sale_price ELSE 0 END), 2)                        AS net_revenue,
        ROUND(
            100.0
            * SUM(CASE WHEN oi.status NOT IN ('Cancelled','Returned')
                       THEN oi.sale_price - p.cost ELSE 0 END)
            / NULLIF(SUM(CASE WHEN oi.status NOT IN ('Cancelled','Returned')
                              THEN oi.sale_price ELSE 0 END), 0.0),
            2
        )                                                                        AS estimated_net_margin_pct
    FROM order_items oi
    JOIN products p ON oi.product_id = p.id
    GROUP BY p.category
),
ranked_orders AS (
    SELECT user_id, order_id,
           ROW_NUMBER() OVER (
               PARTITION BY user_id ORDER BY created_at ASC, order_id ASC
           ) AS order_rank
    FROM orders
),
first_order_ids AS (
    SELECT user_id, order_id FROM ranked_orders WHERE order_rank = 1
),
first_order_categories AS (
    SELECT foi.user_id, p.category,
           SUM(oi.sale_price) AS category_revenue_in_first_order
    FROM first_order_ids foi
    JOIN order_items oi ON foi.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.id
    GROUP BY foi.user_id, p.category
),
user_first_category AS (
    SELECT user_id, category AS first_purchase_category
    FROM (
        SELECT user_id, category,
               ROW_NUMBER() OVER (
                   PARTITION BY user_id
                   ORDER BY category_revenue_in_first_order DESC, category ASC
               ) AS cat_rank
        FROM first_order_categories
    ) t
    WHERE cat_rank = 1
),
user_lifetime AS (
    SELECT
        oi.user_id,
        SUM(CASE WHEN oi.status NOT IN ('Cancelled','Returned')
                 THEN oi.sale_price - p.cost ELSE 0 END)                         AS lifetime_margin,
        SUM(CASE WHEN oi.status NOT IN ('Cancelled','Returned')
                 THEN oi.sale_price ELSE 0 END)                                  AS lifetime_revenue
    FROM order_items oi
    JOIN products p ON oi.product_id = p.id
    GROUP BY oi.user_id
),
category_ltv AS (
    -- Average lifetime margin per first-purchase category (LTV signal)
    SELECT
        ufc.first_purchase_category AS category,
        ROUND(SUM(ul.lifetime_margin) / NULLIF(COUNT(ufc.user_id), 0), 2)       AS avg_lifetime_margin_if_first_purchase
    FROM user_first_category ufc
    JOIN user_lifetime ul ON ufc.user_id = ul.user_id
    GROUP BY ufc.first_purchase_category
),
post_first_items AS (
    SELECT oi.user_id, oi.status, oi.sale_price, p.cost
    FROM order_items oi
    JOIN products p ON oi.product_id = p.id
    LEFT JOIN first_order_ids foi
        ON oi.user_id = foi.user_id AND oi.order_id = foi.order_id
    WHERE foi.order_id IS NULL
),
post_first_value AS (
    SELECT user_id,
           SUM(CASE WHEN status NOT IN ('Cancelled','Returned')
                    THEN sale_price - cost ELSE 0 END)                           AS post_first_margin
    FROM post_first_items
    GROUP BY user_id
),
category_post_first_pct AS (
    -- Share of lifetime margin that comes from orders after the first
    SELECT
        ufc.first_purchase_category AS category,
        ROUND(
            100.0 * SUM(COALESCE(pfv.post_first_margin, 0))
            / NULLIF(SUM(ul.lifetime_margin), 0),
            2
        )                                                                        AS pct_margin_after_first_order
    FROM user_first_category ufc
    JOIN user_lifetime ul ON ufc.user_id = ul.user_id
    LEFT JOIN post_first_value pfv ON ufc.user_id = pfv.user_id
    GROUP BY ufc.first_purchase_category
),
combined AS (
    SELECT
        cm.category,
        cm.net_revenue,
        cm.estimated_net_margin_pct,
        cl.avg_lifetime_margin_if_first_purchase,
        cpf.pct_margin_after_first_order,
        AVG(cm.net_revenue)                           OVER () AS avg_net_revenue,
        AVG(cm.estimated_net_margin_pct)              OVER () AS avg_margin_pct,
        -- AVG ignores NULLs: categories with no LTV data don't distort the average
        AVG(cl.avg_lifetime_margin_if_first_purchase) OVER () AS avg_ltv_margin
    FROM category_metrics cm
    LEFT JOIN category_ltv           cl  ON cm.category = cl.category
    LEFT JOIN category_post_first_pct cpf ON cm.category = cpf.category
),
with_roles AS (
    SELECT
        category,
        net_revenue,
        estimated_net_margin_pct,
        avg_lifetime_margin_if_first_purchase,
        pct_margin_after_first_order,
        CASE
            WHEN net_revenue >= avg_net_revenue AND estimated_net_margin_pct >= avg_margin_pct
                THEN 'Revenue leader'
            WHEN net_revenue >= avg_net_revenue AND estimated_net_margin_pct <  avg_margin_pct
                THEN 'Low-margin volume category'
            WHEN net_revenue <  avg_net_revenue AND estimated_net_margin_pct >= avg_margin_pct
                THEN 'Margin leader'
            WHEN net_revenue <  avg_net_revenue
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
    pct_margin_after_first_order,
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
ORDER BY net_revenue DESC
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def register_views(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(f"CREATE OR REPLACE VIEW orders      AS SELECT * FROM read_csv_auto('{ORDERS}')")
    con.execute(f"CREATE OR REPLACE VIEW order_items AS SELECT * FROM read_csv_auto('{ORDER_ITEMS}')")
    con.execute(f"CREATE OR REPLACE VIEW products    AS SELECT * FROM read_csv_auto('{PRODUCTS}')")


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
    print(f"{len(rows)} rows  ->  {output_path}")
    return len(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

QUERIES = [
    (SQL_CATEGORY_VALUE_RANKING,
     "product_category_value_ranking.csv",
     "Category value ranking"),

    (SQL_REVENUE_MARGIN_QUADRANT,
     "product_revenue_margin_quadrant.csv",
     "Revenue vs margin quadrant"),

    (SQL_FIRST_PURCHASE_CATEGORY_CUSTOMER_VALUE,
     "first_purchase_category_customer_value.csv",
     "First-purchase category customer value"),

    (SQL_FIRST_VS_POST_FIRST_ORDER_VALUE,
     "first_vs_post_first_order_value.csv",
     "First vs post-first order value"),

    (SQL_CATEGORY_RECOMMENDATIONS,
     "product_category_recommendations.csv",
     "Product category recommendations"),
]


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\nE-Commerce Growth Analytics - Product Value Analysis")
    print(f"Source:  {DATA_DIR.resolve()}")
    print(f"Output:  {OUTPUT_DIR.resolve()}")
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
