"""
build_margin_mix_scenarios.py

Margin mix scenario analysis. Uses DuckDB against data/processed/ for platform
baseline metrics, and reads prior analysis CSVs from outputs/tables/ for
category, funnel, and post-purchase inputs.
Writes four output CSVs to outputs/tables/.
Run from the repo root: python src/build_margin_mix_scenarios.py

Scenario model assumptions:
  - Mix shift is zero-sum: total net revenue is unchanged; only the mix between
    low-margin and high-margin categories shifts.
  - Margin rates per category are held constant (no price or cost changes assumed).
  - Lever impact estimates assume historical rates are representative of future
    marginal unit economics.
  - All impact figures are cumulative over the full dataset period (2019-2026, ~7.4 years).
    Annualized figures divide by DATASET_YEARS and represent average annual uplift
    assuming the business maintained a similar run-rate throughout.
"""

from pathlib import Path
import csv
import duckdb

REPO_ROOT   = Path(__file__).parent.parent
DATA_DIR    = REPO_ROOT / "data" / "processed"
TABLES_DIR  = REPO_ROOT / "outputs" / "tables"

ORDER_ITEMS = str(DATA_DIR / "order_items.csv").replace("\\", "/")
PRODUCTS    = str(DATA_DIR / "products.csv").replace("\\", "/")

DATASET_YEARS = 7.4   # approximate span of dataset: 2019 through mid-2026
IMPACT_PERIOD = "Full dataset period, 2019-2026"

CAT_RECS    = str(TABLES_DIR / "product_category_recommendations.csv").replace("\\", "/")
FUNNEL_SRC  = str(TABLES_DIR / "funnel_by_traffic_source.csv").replace("\\", "/")
PP_SUMM     = str(TABLES_DIR / "post_purchase_summary.csv").replace("\\", "/")
PP_CUST     = str(TABLES_DIR / "post_purchase_by_customer_type.csv").replace("\\", "/")


# ---------------------------------------------------------------------------
# SQL
# ---------------------------------------------------------------------------

# Internal baseline — precise platform-level margin metrics.
# total_net_margin: absolute dollars of estimated margin on completed items.
# cancelled/returned_margin_impact: margin that would have been earned, separated
# by loss type (needed to size the cancellation and return reduction levers independently).
SQL_PLATFORM_BASELINE = """
SELECT
    ROUND(SUM(CASE WHEN oi.status NOT IN ('Cancelled','Returned')
                   THEN oi.sale_price - p.cost ELSE 0 END), 2)     AS total_net_margin,
    ROUND(SUM(CASE WHEN oi.status = 'Cancelled'
                   THEN oi.sale_price - p.cost ELSE 0 END), 2)     AS cancelled_margin_impact,
    ROUND(SUM(CASE WHEN oi.status = 'Returned'
                   THEN oi.sale_price - p.cost ELSE 0 END), 2)     AS returned_margin_impact
FROM order_items oi
JOIN products p ON oi.product_id = p.id
"""


# Q1 — Margin mix opportunity.
# One row per category. Shows margin position relative to the platform average
# and revenue share — inputs for identifying where mix shift creates value.
# platform_margin_pct is the revenue-weighted average across all 26 categories
# (derived from the same category CSV, so consistent with category-level figures).
SQL_MARGIN_MIX_OPPORTUNITY = """
WITH platform AS (
    SELECT
        SUM(cr.net_revenue)                                                   AS total_net_revenue,
        SUM(cr.net_revenue * cr.estimated_net_margin_pct / 100.0)             AS total_wtd_margin_dollars
    FROM category_recs cr
)
SELECT
    cr.category,
    cr.strategic_role,
    ROUND(cr.net_revenue, 2)                                                  AS net_revenue,
    ROUND(cr.estimated_net_margin_pct, 2)                                     AS estimated_net_margin_pct,
    ROUND(100.0 * p.total_wtd_margin_dollars / p.total_net_revenue, 2)       AS platform_margin_pct,
    ROUND(cr.estimated_net_margin_pct
          - 100.0 * p.total_wtd_margin_dollars / p.total_net_revenue, 2)     AS margin_gap_pp,
    ROUND(100.0 * cr.net_revenue / p.total_net_revenue, 2)                   AS revenue_share_pct
FROM category_recs cr
CROSS JOIN platform p
ORDER BY
    CASE cr.strategic_role
        WHEN 'Low-margin volume category'      THEN 1
        WHEN 'Margin leader'                   THEN 2
        WHEN 'Revenue leader'                  THEN 3
        WHEN 'High-value acquisition category' THEN 4
        ELSE 5
    END,
    cr.net_revenue DESC
"""


# Q2 — Scenario margin uplift.
# Models shifting 1%, 5%, and 10% of low-margin volume category net revenue
# to margin leader categories (zero-sum: total net revenue unchanged).
# Margin gain = shifted_revenue × (wtd_avg_margin_leader_pct − wtd_avg_low_margin_pct).
# margin_uplift_pct_of_baseline = gain expressed as % of total baseline margin.
SQL_SCENARIO_UPLIFT = f"""
WITH role_metrics AS (
    SELECT
        cr.strategic_role,
        SUM(cr.net_revenue)                                                           AS role_net_revenue,
        100.0 * SUM(cr.net_revenue * cr.estimated_net_margin_pct / 100.0)
                / NULLIF(SUM(cr.net_revenue), 0)                                      AS weighted_margin_pct
    FROM category_recs cr
    WHERE cr.strategic_role IN ('Low-margin volume category', 'Margin leader')
    GROUP BY cr.strategic_role
),
low_margin  AS (SELECT role_net_revenue AS lm_revenue,  weighted_margin_pct AS lm_pct
                FROM role_metrics WHERE strategic_role = 'Low-margin volume category'),
high_margin AS (SELECT weighted_margin_pct AS hm_pct
                FROM role_metrics WHERE strategic_role = 'Margin leader'),
platform AS (
    SELECT
        SUM(cr.net_revenue)                                                            AS total_net_revenue,
        SUM(cr.net_revenue * cr.estimated_net_margin_pct / 100.0)                     AS total_wtd_margin
    FROM category_recs cr
),
scenarios(shift_pct) AS (VALUES (1), (5), (10))
SELECT
    s.shift_pct,
    ROUND(lm.lm_revenue * s.shift_pct / 100.0, 2)                                     AS revenue_shifted,
    ROUND(lm.lm_pct, 2)                                                                AS low_margin_category_avg_pct,
    ROUND(hm.hm_pct, 2)                                                                AS high_margin_category_avg_pct,
    ROUND(lm.lm_revenue * s.shift_pct / 100.0
          * (hm.hm_pct - lm.lm_pct) / 100.0, 2)                                       AS estimated_margin_gain,
    ROUND((lm.lm_revenue * s.shift_pct / 100.0
           * (hm.hm_pct - lm.lm_pct) / 100.0) / {DATASET_YEARS}, 2)                  AS estimated_margin_gain_annualized,
    'Full dataset period, 2019-2026'                                                   AS impact_period,
    ROUND(p.total_wtd_margin, 2)                                                       AS baseline_total_margin,
    ROUND(p.total_wtd_margin
          + lm.lm_revenue * s.shift_pct / 100.0
            * (hm.hm_pct - lm.lm_pct) / 100.0, 2)                                    AS new_total_margin,
    ROUND(100.0 * p.total_wtd_margin / p.total_net_revenue, 2)                        AS baseline_margin_pct,
    ROUND(100.0 * (p.total_wtd_margin
          + lm.lm_revenue * s.shift_pct / 100.0
            * (hm.hm_pct - lm.lm_pct) / 100.0)
          / p.total_net_revenue, 2)                                                    AS new_margin_pct,
    ROUND(100.0 * (lm.lm_revenue * s.shift_pct / 100.0
                   * (hm.hm_pct - lm.lm_pct) / 100.0)
          / NULLIF(p.total_wtd_margin, 0), 2)                                         AS margin_uplift_pct_of_baseline
FROM scenarios s
CROSS JOIN low_margin lm
CROSS JOIN high_margin hm
CROSS JOIN platform p
ORDER BY s.shift_pct
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def register_views(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(f"CREATE OR REPLACE VIEW order_items   AS SELECT * FROM read_csv_auto('{ORDER_ITEMS}')")
    con.execute(f"CREATE OR REPLACE VIEW products      AS SELECT * FROM read_csv_auto('{PRODUCTS}')")
    con.execute(f"CREATE OR REPLACE VIEW category_recs AS SELECT * FROM read_csv_auto('{CAT_RECS}')")
    con.execute(f"CREATE OR REPLACE VIEW funnel        AS SELECT * FROM read_csv_auto('{FUNNEL_SRC}')")
    con.execute(f"CREATE OR REPLACE VIEW pp_summary    AS SELECT * FROM read_csv_auto('{PP_SUMM}')")
    con.execute(f"CREATE OR REPLACE VIEW pp_cust       AS SELECT * FROM read_csv_auto('{PP_CUST}')")


def run_query(
    con: duckdb.DuckDBPyConnection,
    sql: str,
    output_path: Path,
    label: str,
) -> tuple[int, list]:
    print(f"  {label} ...", end=" ", flush=True)
    result = con.execute(sql)
    cols   = [d[0] for d in result.description]
    rows   = result.fetchall()
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(cols)
        writer.writerows(rows)
    print(f"{len(rows)} rows  ->  {output_path.name}")
    return len(rows), rows


def write_csv(rows: list[dict], output_path: Path, label: str) -> int:
    """Write a list-of-dicts to CSV."""
    print(f"  {label} ...", end=" ", flush=True)
    if not rows:
        print("0 rows  (empty)")
        return 0
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} rows  ->  {output_path.name}")
    return len(rows)


# ---------------------------------------------------------------------------
# Growth lever scorecard (Python, uses DuckDB baseline + scenario results)
# ---------------------------------------------------------------------------

# math_confidence:      how precisely the impact arithmetic can be derived from the data.
# execution_confidence: how confident we are the lever can actually be moved to that scenario.
# feasibility_rating:   how tractable the lever is in practice (investment / difficulty).
# assumption_note:      the single biggest assumption embedded in the impact estimate.
# All use High / Medium / Low.

_MIX_ASSUMPTION = (
    "Assumes demand is fully transferable between categories at constant margin rates "
    "(zero-sum revenue shift). Fashion demand is category-sticky; real mix shifts "
    "typically require changes to new-customer acquisition mix, not conversion of "
    "existing buyers."
)
_CART_ASSUMPTION = (
    "Assumes marginal recovered sessions have average purchase margin ($23.30/session). "
    "Non-converting cart sessions may be more price-sensitive or have lower-value items, "
    "making true marginal margin lower than the historical average."
)
_REPEAT_ASSUMPTION = (
    "Assumes incremental repeat orders match the economics of historical repeat orders "
    "(avg $65.48 net revenue, platform blended margin rate 51.9%). Reactivated one-time "
    "buyers may produce smaller or lower-margin initial repeat orders."
)
_CANCEL_ASSUMPTION = (
    "Assumes recovered items complete at the average margin of historical cancelled items "
    "($31.11/item). Does not account for fulfillment costs already incurred at cancellation. "
    "Root cause of the 15% cancellation rate is not captured in this dataset."
)
_RETURN_ASSUMPTION = (
    "Assumes prevented returns retain the average margin of historical returned items "
    "($30.99/item). Return reasons are not captured in this dataset, so the intervention "
    "required to achieve this reduction is undefined."
)

LEVER_META = {
    "mix_1pct":    {"math_confidence": "Medium", "execution_confidence": "Low",    "feasibility_rating": "Medium", "notes": "Modest demand shift via merchandising; requires A/B test to validate revenue transfer",    "assumption_note": _MIX_ASSUMPTION},
    "mix_5pct":    {"math_confidence": "Medium", "execution_confidence": "Low",    "feasibility_rating": "Low",    "notes": "Significant demand shift; needs sustained merchandising and acquisition changes",           "assumption_note": _MIX_ASSUMPTION},
    "mix_10pct":   {"math_confidence": "Medium", "execution_confidence": "Low",    "feasibility_rating": "Low",    "notes": "Major repositioning; multi-quarter initiative, high execution risk",                       "assumption_note": _MIX_ASSUMPTION},
    "cart_1pp":    {"math_confidence": "High",   "execution_confidence": "Medium", "feasibility_rating": "High",   "notes": "Directly measurable; checkout UX or cart-reminder email A/B test",                        "assumption_note": _CART_ASSUMPTION},
    "cart_5pp":    {"math_confidence": "High",   "execution_confidence": "Low",    "feasibility_rating": "Medium", "notes": "Requires systematic checkout optimization across all sources",                            "assumption_note": _CART_ASSUMPTION},
    "repeat_5pct": {"math_confidence": "Medium", "execution_confidence": "Medium", "feasibility_rating": "High",   "notes": "Email/loyalty re-engagement for 1-time buyers; well-proven playbook",                     "assumption_note": _REPEAT_ASSUMPTION},
    "repeat_10pct":{"math_confidence": "Medium", "execution_confidence": "Low",    "feasibility_rating": "Medium", "notes": "Sustained retention program needed beyond single campaign",                               "assumption_note": _REPEAT_ASSUMPTION},
    "cancel_1pp":  {"math_confidence": "High",   "execution_confidence": "Low",    "feasibility_rating": "Medium", "notes": "Root cause varies; intervention design requires cancellation reason data",                 "assumption_note": _CANCEL_ASSUMPTION},
    "cancel_3pp":  {"math_confidence": "Medium", "execution_confidence": "Low",    "feasibility_rating": "Low",    "notes": "Structural change needed; root cause likely multi-factor",                                "assumption_note": _CANCEL_ASSUMPTION},
    "return_1pp":  {"math_confidence": "High",   "execution_confidence": "Low",    "feasibility_rating": "Medium", "notes": "Better product descriptions and sizing guidance; testable by category",                   "assumption_note": _RETURN_ASSUMPTION},
    "return_3pp":  {"math_confidence": "Medium", "execution_confidence": "Low",    "feasibility_rating": "Low",    "notes": "Requires product quality improvements and deeper UX changes",                             "assumption_note": _RETURN_ASSUMPTION},
}

FEASIBILITY_SCORE = {"High": 3, "Medium": 2, "Low": 1}


def build_scorecard(con: duckdb.DuckDBPyConnection, scenario_rows: list) -> list[dict]:
    # --- Platform baseline ---
    b = con.execute(SQL_PLATFORM_BASELINE).fetchone()
    total_net_margin      = float(b[0])
    cancelled_marg_impact = float(b[1])
    returned_marg_impact  = float(b[2])

    pp_result  = con.execute("SELECT * FROM pp_summary").fetchone()
    pp_cols    = [d[0] for d in con.execute("SELECT * FROM pp_summary").description]
    pp         = dict(zip(pp_cols, pp_result))
    total_net_revenue   = float(pp["net_revenue"])
    total_items         = float(pp["total_items"])
    cancellation_rate   = float(pp["cancellation_rate"])   # percent
    return_rate         = float(pp["return_rate"])          # percent

    funnel_agg = con.execute(
        "SELECT SUM(cart_sessions) AS tc, SUM(purchase_sessions) AS tp FROM funnel"
    ).fetchone()
    total_cart_sessions      = float(funnel_agg[0])
    total_purchase_sessions  = float(funnel_agg[1])

    repeat_row = con.execute(
        "SELECT net_revenue, orders FROM pp_cust WHERE customer_type LIKE 'Repeat%'"
    ).fetchone()
    repeat_net_revenue = float(repeat_row[0])
    repeat_orders      = float(repeat_row[1])

    # Derived unit economics
    platform_margin_rate       = total_net_margin / total_net_revenue
    avg_margin_per_purchase    = total_net_margin / total_purchase_sessions
    avg_repeat_order_margin    = (repeat_net_revenue * platform_margin_rate) / repeat_orders
    cancelled_items            = total_items * cancellation_rate / 100.0
    returned_items             = total_items * return_rate / 100.0
    margin_per_cancelled_item  = cancelled_marg_impact / cancelled_items
    margin_per_returned_item   = returned_marg_impact  / returned_items

    # --- Lever impact estimates ---
    # scenario_rows columns: shift_pct, revenue_shifted, lm_pct, hm_pct,
    #   estimated_margin_gain, baseline_margin, new_margin, baseline_pct, new_pct, uplift_pct_of_baseline
    scenario_gain = {int(row[0]): float(row[4]) for row in scenario_rows}

    lever_impacts = {
        "mix_1pct":    ("Margin mix shift 1%",              "Mix shift",           "1% of low-margin rev → margin leaders",    round(scenario_gain[1],  2)),
        "mix_5pct":    ("Margin mix shift 5%",              "Mix shift",           "5% of low-margin rev → margin leaders",    round(scenario_gain[5],  2)),
        "mix_10pct":   ("Margin mix shift 10%",             "Mix shift",           "10% of low-margin rev → margin leaders",   round(scenario_gain[10], 2)),
        "cart_1pp":    ("Cart → purchase rate +1pp",        "Conversion",          "+1pp cart-to-purchase rate",               round(total_cart_sessions * 0.01 * avg_margin_per_purchase, 2)),
        "cart_5pp":    ("Cart → purchase rate +5pp",        "Conversion",          "+5pp cart-to-purchase rate",               round(total_cart_sessions * 0.05 * avg_margin_per_purchase, 2)),
        "repeat_5pct": ("Repeat orders +5%",                "Retention",           "+5% more repeat purchase orders",          round(repeat_orders * 0.05 * avg_repeat_order_margin, 2)),
        "repeat_10pct":("Repeat orders +10%",               "Retention",           "+10% more repeat purchase orders",         round(repeat_orders * 0.10 * avg_repeat_order_margin, 2)),
        "cancel_1pp":  ("Cancellation rate −1pp",           "Post-purchase",       "Recover 1pp worth of cancelled items",     round(total_items * 0.01 * margin_per_cancelled_item, 2)),
        "cancel_3pp":  ("Cancellation rate −3pp",           "Post-purchase",       "Recover 3pp worth of cancelled items",     round(total_items * 0.03 * margin_per_cancelled_item, 2)),
        "return_1pp":  ("Return rate −1pp",                 "Post-purchase",       "Recover 1pp worth of returned items",      round(total_items * 0.01 * margin_per_returned_item, 2)),
        "return_3pp":  ("Return rate −3pp",                 "Post-purchase",       "Recover 3pp worth of returned items",      round(total_items * 0.03 * margin_per_returned_item, 2)),
    }

    # Rank by impact × feasibility score (higher = better)
    rows = []
    for key, (lever, lever_type, scenario_desc, uplift) in lever_impacts.items():
        m = LEVER_META[key]
        rows.append({
            "lever":                              lever,
            "lever_type":                         lever_type,
            "scenario":                           scenario_desc,
            "impact_period":                      IMPACT_PERIOD,
            "estimated_margin_uplift":            uplift,
            "estimated_margin_uplift_annualized": round(uplift / DATASET_YEARS, 2),
            "math_confidence":                    m["math_confidence"],
            "execution_confidence":               m["execution_confidence"],
            "feasibility_rating":                 m["feasibility_rating"],
            "assumption_note":                    m["assumption_note"],
            "notes":                              m["notes"],
        })

    rows.sort(
        key=lambda r: r["estimated_margin_uplift"] * FEASIBILITY_SCORE[r["feasibility_rating"]],
        reverse=True,
    )
    for rank, row in enumerate(rows, 1):
        row["priority_rank"] = rank

    # Reorder columns with rank first
    ordered = []
    for row in rows:
        ordered.append({
            "priority_rank":                      row["priority_rank"],
            "lever":                              row["lever"],
            "lever_type":                         row["lever_type"],
            "scenario":                           row["scenario"],
            "impact_period":                      row["impact_period"],
            "estimated_margin_uplift":            row["estimated_margin_uplift"],
            "estimated_margin_uplift_annualized": row["estimated_margin_uplift_annualized"],
            "math_confidence":                    row["math_confidence"],
            "execution_confidence":               row["execution_confidence"],
            "feasibility_rating":                 row["feasibility_rating"],
            "assumption_note":                    row["assumption_note"],
            "notes":                              row["notes"],
        })
    return ordered


# ---------------------------------------------------------------------------
# Recommended experiments (Python, driven by scorecard)
# ---------------------------------------------------------------------------

def build_experiments(scorecard_rows: list[dict]) -> list[dict]:
    # Select the 3 highest-priority levers with feasibility >= Medium.
    # Map each to a concrete experiment definition.
    experiment_map = {
        "Conversion":    {
            "experiment_name":         "Cart abandonment email A/B test",
            "hypothesis":              "A timed cart-reminder email to non-converting cart sessions will recover a measurable share of abandoned carts and lift the cart-to-purchase rate by at least 1pp.",
            "key_metric":              "Cart-to-purchase rate; margin per cart session",
        },
        "Retention":     {
            "experiment_name":         "One-time buyer re-engagement campaign",
            "hypothesis":              "A targeted email sequence sent to customers with exactly one lifetime order will increase repeat purchase rate, recovering a portion of the ~63% one-time buyer population.",
            "key_metric":              "Repeat order rate (90-day window); incremental net margin per re-engaged customer",
        },
        "Mix shift":     {
            "experiment_name":         "High-margin category visibility test",
            "hypothesis":              "Increasing search ranking and browse placement for Blazers & Jackets and Accessories — the two highest-margin underscaled categories — will shift a portion of demand from lower-margin categories and improve blended margin pct.",
            "key_metric":              "Category revenue share; blended estimated margin pct; no drop in total session purchase rate",
        },
        "Post-purchase": {
            "experiment_name":         "Cancellation root cause investigation and pre-cancellation intervention pilot",
            "hypothesis":              "Surfacing an order-status update or proactive offer (e.g., estimated delivery reassurance) to customers showing pre-cancellation signals will reduce cancellation rate by at least 1pp.",
            "key_metric":              "Cancellation rate; recovered margin per intervention cohort",
        },
    }

    seen_types = set()
    experiments = []
    priority = 1

    for row in scorecard_rows:
        ltype = row["lever_type"]
        if ltype in seen_types:
            continue
        if row["feasibility_rating"] == "Low":
            continue
        if ltype not in experiment_map:
            continue
        exp = experiment_map[ltype]
        experiments.append({
            "priority":                              priority,
            "experiment_name":                       exp["experiment_name"],
            "lever_type":                            ltype,
            "hypothesis":                            exp["hypothesis"],
            "key_metric":                            exp["key_metric"],
            "impact_period":                         IMPACT_PERIOD,
            "estimated_margin_uplift":               row["estimated_margin_uplift"],
            "estimated_margin_uplift_annualized":    row["estimated_margin_uplift_annualized"],
            "math_confidence":                       row["math_confidence"],
            "execution_confidence":                  row["execution_confidence"],
            "feasibility_rating":                    row["feasibility_rating"],
        })
        seen_types.add(ltype)
        priority += 1
        if priority > 3:
            break

    return experiments


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    print("\nE-Commerce Growth Analytics - Margin Mix Scenario Analysis")
    print(f"Data source:  {DATA_DIR}")
    print(f"Prior CSVs:   {TABLES_DIR}")
    print(f"Output:       {TABLES_DIR}")
    print("\nRunning queries and computing scenarios:\n")

    con = duckdb.connect()
    register_views(con)

    total_rows = 0

    # Q1 — Margin mix opportunity
    n, _ = run_query(con, SQL_MARGIN_MIX_OPPORTUNITY,
                     TABLES_DIR / "margin_mix_opportunity.csv",
                     "Margin mix opportunity")
    total_rows += n

    # Q2 — Scenario margin uplift
    n, scenario_rows = run_query(con, SQL_SCENARIO_UPLIFT,
                                 TABLES_DIR / "scenario_margin_uplift.csv",
                                 "Scenario margin uplift")
    total_rows += n

    # Q3 — Growth lever scorecard (Python, uses DuckDB baseline + scenario rows)
    print("  Growth lever scorecard ...", end=" ", flush=True)
    scorecard = build_scorecard(con, scenario_rows)
    con.close()
    path = TABLES_DIR / "growth_lever_scorecard.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=scorecard[0].keys())
        writer.writeheader()
        writer.writerows(scorecard)
    print(f"{len(scorecard)} rows  ->  {path.name}")
    total_rows += len(scorecard)

    # Q4 — Recommended experiments (Python, driven by scorecard)
    experiments = build_experiments(scorecard)
    n = write_csv(experiments, TABLES_DIR / "recommended_experiments.csv",
                  "Recommended experiments")
    total_rows += n

    print(f"\nDone. 4 files written, {total_rows:,} total rows.")


if __name__ == "__main__":
    main()
