"""
build_funnel_analysis.py

Runs conversion / funnel analysis against data/processed/ using DuckDB.
Writes four output CSVs to outputs/tables/.
Run from the repo root: python src/build_funnel_analysis.py

Event type reference (confirmed from data):
  product     — product detail page view  (URI: /product/NNN)
  cart        — cart view / add-to-cart   (URI: /cart)
  department  — category browse page      (URI: /department/...)
  purchase    — completed purchase        (URI: /purchase)
  cancel      — order cancellation        (URI: /cancel)
  home        — home page                 (URI: /home)

Traffic sources: Email, Adwords, YouTube, Facebook, Organic
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

EVENTS      = str(DATA_DIR / "events.csv").replace("\\", "/")
ORDERS      = str(DATA_DIR / "orders.csv").replace("\\", "/")
ORDER_ITEMS = str(DATA_DIR / "order_items.csv").replace("\\", "/")
PRODUCTS    = str(DATA_DIR / "products.csv").replace("\\", "/")


# ---------------------------------------------------------------------------
# SQL
# ---------------------------------------------------------------------------

# Q1 — Session funnel by traffic source.
# One row per traffic source.
# traffic_source is taken from the earliest event in the session (by created_at).
# Funnel stages:
#   browse_sessions    — sessions with at least one product-page view
#   cart_sessions      — sessions with at least one cart event
#   purchase_sessions  — sessions with at least one purchase event
# Rates:
#   browse_to_cart_rate    = cart_sessions  / browse_sessions
#   cart_to_purchase_rate  = purchase_sessions / cart_sessions
#   session_purchase_rate  = purchase_sessions / total sessions
SQL_FUNNEL_BY_TRAFFIC_SOURCE = """
WITH
session_source AS (
    -- One traffic_source per session: the source from the earliest event
    SELECT session_id, traffic_source
    FROM (
        SELECT
            session_id,
            traffic_source,
            ROW_NUMBER() OVER (PARTITION BY session_id ORDER BY created_at ASC) AS rn
        FROM events
    ) t
    WHERE rn = 1
),
session_flags AS (
    -- One row per session with a flag for each funnel stage
    SELECT
        session_id,
        MAX(CASE WHEN event_type = 'product'  THEN 1 ELSE 0 END) AS has_browse,
        MAX(CASE WHEN event_type = 'cart'     THEN 1 ELSE 0 END) AS has_cart,
        MAX(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS has_purchase
    FROM events
    GROUP BY session_id
),
sessions AS (
    SELECT
        sf.session_id,
        ss.traffic_source,
        sf.has_browse,
        sf.has_cart,
        sf.has_purchase
    FROM session_flags sf
    JOIN session_source ss ON sf.session_id = ss.session_id
)
SELECT
    traffic_source,
    COUNT(*)                                                                      AS sessions,
    SUM(has_browse)                                                               AS browse_sessions,
    SUM(has_cart)                                                                 AS cart_sessions,
    SUM(has_purchase)                                                             AS purchase_sessions,
    ROUND(100.0 * SUM(has_cart)     / NULLIF(SUM(has_browse),  0), 2)            AS browse_to_cart_rate,
    ROUND(100.0 * SUM(has_purchase) / NULLIF(SUM(has_cart),    0), 2)            AS cart_to_purchase_rate,
    ROUND(100.0 * SUM(has_purchase) / NULLIF(COUNT(*),         0), 2)            AS session_purchase_rate
FROM sessions
GROUP BY traffic_source
ORDER BY sessions DESC
"""


# Q2 — Event type distribution.
# One row per event type. Shows how events are distributed across funnel stages.
SQL_EVENT_TYPE_DISTRIBUTION = """
WITH total AS (
    SELECT COUNT(*) AS total_events FROM events
)
SELECT
    event_type,
    COUNT(*)                                                     AS event_count,
    ROUND(100.0 * COUNT(*) / MAX(t.total_events), 2)            AS pct_of_total
FROM events
CROSS JOIN total t
GROUP BY event_type
ORDER BY event_count DESC
"""


# Q3 — Session purchase summary.
# Single aggregate row: total sessions, purchasing vs non-purchasing, overall rate.
SQL_SESSION_PURCHASE_SUMMARY = """
WITH session_flags AS (
    SELECT
        session_id,
        MAX(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS has_purchase
    FROM events
    GROUP BY session_id
)
SELECT
    COUNT(*)                                                       AS total_sessions,
    SUM(has_purchase)                                              AS purchasing_sessions,
    COUNT(*) - SUM(has_purchase)                                   AS non_purchasing_sessions,
    ROUND(100.0 * SUM(has_purchase) / NULLIF(COUNT(*), 0), 2)     AS session_purchase_rate
FROM session_flags
"""


# Q4 — High-value category funnel.
# Compares funnel behavior for sessions that included a product-page view of a
# Revenue leader category vs all other sessions.
#
# Revenue leader categories come from the Phase 3 product value analysis:
#   Outerwear & Coats, Suits & Sport Coats, Sweaters, Sleep & Lounge,
#   Active, Dresses, Pants
#
# Product IDs are extracted from product event URIs, which follow the confirmed
# format: /product/NNN (e.g. /product/12345). Non-matching URIs yield NULL and
# are excluded from the category join.
SQL_HIGH_VALUE_CATEGORY_FUNNEL = """
WITH
product_view_ids AS (
    -- Extract product_id from product-page URIs (/product/NNN)
    SELECT
        session_id,
        TRY_CAST(regexp_extract(uri, '/product/(\\d+)', 1) AS INTEGER) AS product_id
    FROM events
    WHERE event_type = 'product'
),
hv_session_ids AS (
    -- Sessions containing at least one product view for a Revenue leader category
    SELECT DISTINCT pvi.session_id
    FROM product_view_ids pvi
    JOIN products p ON pvi.product_id = p.id
    WHERE pvi.product_id IS NOT NULL
      AND p.category IN (
          'Outerwear & Coats',
          'Suits & Sport Coats',
          'Sweaters',
          'Sleep & Lounge',
          'Active',
          'Dresses',
          'Pants'
      )
),
session_flags AS (
    SELECT
        session_id,
        MAX(CASE WHEN event_type = 'product'  THEN 1 ELSE 0 END) AS has_browse,
        MAX(CASE WHEN event_type = 'cart'     THEN 1 ELSE 0 END) AS has_cart,
        MAX(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS has_purchase
    FROM events
    GROUP BY session_id
)
SELECT
    CASE
        WHEN hv.session_id IS NOT NULL THEN 'Revenue leader category session'
        ELSE 'Other session'
    END                                                                            AS session_type,
    COUNT(*)                                                                       AS sessions,
    SUM(sf.has_browse)                                                             AS browse_sessions,
    SUM(sf.has_cart)                                                               AS cart_sessions,
    SUM(sf.has_purchase)                                                           AS purchase_sessions,
    ROUND(100.0 * SUM(sf.has_cart)     / NULLIF(SUM(sf.has_browse), 0), 2)        AS browse_to_cart_rate,
    ROUND(100.0 * SUM(sf.has_purchase) / NULLIF(SUM(sf.has_cart),   0), 2)        AS cart_to_purchase_rate,
    ROUND(100.0 * SUM(sf.has_purchase) / NULLIF(COUNT(*),           0), 2)        AS session_purchase_rate
FROM session_flags sf
LEFT JOIN hv_session_ids hv ON sf.session_id = hv.session_id
GROUP BY 1
ORDER BY sessions DESC
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def register_views(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(f"CREATE OR REPLACE VIEW events      AS SELECT * FROM read_csv_auto('{EVENTS}')")
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
    print(f"{len(rows)} rows  ->  {output_path.name}")
    return len(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

QUERIES = [
    (SQL_FUNNEL_BY_TRAFFIC_SOURCE,
     "funnel_by_traffic_source.csv",
     "Funnel by traffic source"),

    (SQL_EVENT_TYPE_DISTRIBUTION,
     "event_type_distribution.csv",
     "Event type distribution"),

    (SQL_SESSION_PURCHASE_SUMMARY,
     "session_purchase_summary.csv",
     "Session purchase summary"),

    (SQL_HIGH_VALUE_CATEGORY_FUNNEL,
     "high_value_category_funnel.csv",
     "High-value category funnel"),
]


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\nE-Commerce Growth Analytics - Funnel Analysis")
    print(f"Source:  {DATA_DIR}")
    print(f"Output:  {OUTPUT_DIR}")
    print(f"\nRunning {len(QUERIES)} queries (events.csv = 2.4M rows, may take ~30s):\n")

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
