"""
build_tableau_exports.py

Creates clean Tableau-ready CSVs from existing outputs/tables/ analysis outputs.
Feeds the 3-tab portfolio dashboard: Executive Overview, Growth Leaks, Action Plan.
Writes 5 output CSVs to outputs/tableau/.
Run from the repo root: python src/build_tableau_exports.py

Inputs (all from outputs/tables/):
  overall_business_summary.csv
  post_purchase_summary.csv
  customer_purchase_summary.csv
  funnel_by_traffic_source.csv
  experiment_priority_matrix.csv
  growth_lever_scorecard.csv

Outputs (to outputs/tableau/):
  executive_kpis.csv             - KPI tiles for Executive Overview tab
  waterfall_data.csv             - Gantt-ready unit economics waterfall stages
  funnel_summary.csv             - Aggregated 3-stage funnel for Growth Leaks tab
  buyer_split.csv                - One-time vs. repeat buyer breakdown
  action_plan_kpis.csv           - KPI tiles for Action Plan tab
  growth_lever_scorecard.csv     - Lever scorecard for Action Plan tab (fields trimmed)
  experiment_priority_matrix.csv - Experiment priority table for Action Plan tab
"""

from pathlib import Path
import csv

REPO_ROOT   = Path(__file__).parent.parent
TABLES_DIR  = REPO_ROOT / "outputs" / "tables"
TABLEAU_DIR = REPO_ROOT / "outputs" / "tableau"


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def read_csv(filename: str) -> list[dict]:
    # utf-8-sig strips the BOM present in BigQuery-exported CSVs
    with open(TABLES_DIR / filename, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_tableau_csv(rows: list[dict], filename: str) -> int:
    print(f"  {filename} ...", end=" ", flush=True)
    if not rows:
        print("0 rows  (empty)")
        return 0
    path = TABLEAU_DIR / filename
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} rows")
    return len(rows)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def fmt_millions(val: float) -> str:
    return f"${val / 1_000_000:.2f}M"


def fmt_currency_k(val: float) -> str:
    return f"~${round(val / 1_000)}K/yr"


def fmt_pct(val: float) -> str:
    return f"{val:.1f}%"


def fmt_int(val: float) -> str:
    return f"{int(val):,}"


# ---------------------------------------------------------------------------
# 1. executive_kpis.csv
# ---------------------------------------------------------------------------

def build_executive_kpis() -> list[dict]:
    summary = read_csv("overall_business_summary.csv")[0]
    pp      = read_csv("post_purchase_summary.csv")[0]

    gross_rev    = float(summary["gross_revenue"])
    net_margin   = float(summary["estimated_net_margin"])
    total_orders = int(float(summary["total_orders"]))
    total_buyers = int(float(summary["total_buyers"]))

    cancelled_rev = float(pp["cancelled_revenue"])
    returned_rev  = float(pp["returned_revenue"])
    pp_gross      = float(pp["gross_revenue"])
    loss_rate     = (cancelled_rev + returned_rev) / pp_gross * 100

    return [
        {
            "kpi_name":       "Gross Revenue",
            "kpi_value":      round(gross_rev, 2),
            "formatted_value": fmt_millions(gross_rev),
            "sort_order":     1,
            "dashboard_tab":  "Executive Overview",
        },
        {
            "kpi_name":       "Est. Net Margin",
            "kpi_value":      round(net_margin, 2),
            "formatted_value": fmt_millions(net_margin),
            "sort_order":     2,
            "dashboard_tab":  "Executive Overview",
        },
        {
            "kpi_name":       "Combined Loss Rate",
            "kpi_value":      round(loss_rate, 1),
            "formatted_value": fmt_pct(loss_rate),
            "sort_order":     3,
            "dashboard_tab":  "Executive Overview",
        },
        {
            "kpi_name":       "Total Orders",
            "kpi_value":      total_orders,
            "formatted_value": fmt_int(total_orders),
            "sort_order":     4,
            "dashboard_tab":  "Executive Overview",
        },
        {
            "kpi_name":       "Total Buyers",
            "kpi_value":      total_buyers,
            "formatted_value": fmt_int(total_buyers),
            "sort_order":     5,
            "dashboard_tab":  "Executive Overview",
        },
    ]


# ---------------------------------------------------------------------------
# 2. waterfall_data.csv
# ---------------------------------------------------------------------------

def build_waterfall_data() -> list[dict]:
    summary = read_csv("overall_business_summary.csv")[0]
    pp      = read_csv("post_purchase_summary.csv")[0]

    gross_rev    = float(pp["gross_revenue"])
    cancelled_rev = float(pp["cancelled_revenue"])
    returned_rev  = float(pp["returned_revenue"])
    net_rev       = float(pp["net_revenue"])
    net_cost      = float(summary["estimated_net_cost"])
    net_margin    = float(summary["estimated_net_margin"])

    after_cancel = gross_rev - cancelled_rev

    return [
        {
            "stage_label":    "Gross Revenue",
            "stage_order":    1,
            "bar_value":      round(gross_rev, 2),
            "running_start":  0,
            "bar_type":       "total",
            "formatted_label": fmt_millions(gross_rev),
        },
        {
            "stage_label":    "Cancellations",
            "stage_order":    2,
            "bar_value":      round(-cancelled_rev, 2),
            "running_start":  round(gross_rev, 2),
            "bar_type":       "decrease",
            "formatted_label": f"-{fmt_millions(cancelled_rev)}",
        },
        {
            "stage_label":    "Returns",
            "stage_order":    3,
            "bar_value":      round(-returned_rev, 2),
            "running_start":  round(after_cancel, 2),
            "bar_type":       "decrease",
            "formatted_label": f"-{fmt_millions(returned_rev)}",
        },
        {
            "stage_label":    "Net Revenue",
            "stage_order":    4,
            "bar_value":      round(net_rev, 2),
            "running_start":  0,
            "bar_type":       "subtotal",
            "formatted_label": fmt_millions(net_rev),
        },
        {
            "stage_label":    "Est. Product Cost",
            "stage_order":    5,
            "bar_value":      round(-net_cost, 2),
            "running_start":  round(net_rev, 2),
            "bar_type":       "decrease",
            "formatted_label": f"-{fmt_millions(net_cost)}",
        },
        {
            "stage_label":    "Net Margin",
            "stage_order":    6,
            "bar_value":      round(net_margin, 2),
            "running_start":  0,
            "bar_type":       "total",
            "formatted_label": fmt_millions(net_margin),
        },
    ]


# ---------------------------------------------------------------------------
# 3. funnel_summary.csv
# ---------------------------------------------------------------------------

def build_funnel_summary() -> list[dict]:
    funnel_rows = read_csv("funnel_by_traffic_source.csv")

    total_sessions = sum(int(r["sessions"])          for r in funnel_rows)
    total_cart     = sum(int(r["cart_sessions"])      for r in funnel_rows)
    total_purchase = sum(int(r["purchase_sessions"])  for r in funnel_rows)

    browse_to_cart_rate   = total_cart     / total_sessions * 100
    cart_to_purchase_rate = total_purchase / total_cart     * 100
    cart_abandonment_rate = 100 - cart_to_purchase_rate

    return [
        {
            "funnel_stage":    "Total Sessions",
            "stage_order":     1,
            "session_count":   total_sessions,
            "pct_of_previous": "",
            "drop_label":      "",
        },
        {
            "funnel_stage":    "Added to Cart",
            "stage_order":     2,
            "session_count":   total_cart,
            "pct_of_previous": round(browse_to_cart_rate, 1),
            "drop_label":      f"{browse_to_cart_rate:.1f}% of sessions added to cart",
        },
        {
            "funnel_stage":    "Completed Purchase",
            "stage_order":     3,
            "session_count":   total_purchase,
            "pct_of_previous": round(cart_to_purchase_rate, 1),
            "drop_label":      (
                f"{cart_to_purchase_rate:.1f}% of cart sessions purchased - "
                f"{cart_abandonment_rate:.1f}% abandoned"
            ),
        },
    ]


# ---------------------------------------------------------------------------
# 4. buyer_split.csv
# ---------------------------------------------------------------------------

def build_buyer_split() -> list[dict]:
    cust = read_csv("customer_purchase_summary.csv")[0]

    one_time      = int(float(cust["one_time_buyers"]))
    repeat        = int(float(cust["repeat_buyers"]))
    repeat_rate   = float(cust["repeat_buyer_rate"])
    one_time_rate = float(cust["one_time_buyer_rate"])

    return [
        {
            "buyer_type":      "One-Time Buyers",
            "buyer_count":     one_time,
            "buyer_rate":      round(one_time_rate, 1),
            "formatted_label": f"{one_time:,} ({one_time_rate:.1f}%)",
            "sort_order":      1,
        },
        {
            "buyer_type":      "Repeat Buyers",
            "buyer_count":     repeat,
            "buyer_rate":      round(repeat_rate, 1),
            "formatted_label": f"{repeat:,} ({repeat_rate:.1f}%)",
            "sort_order":      2,
        },
    ]


# ---------------------------------------------------------------------------
# 5. action_plan_kpis.csv
# ---------------------------------------------------------------------------

def build_action_plan_kpis() -> list[dict]:
    exp_rows = read_csv("experiment_priority_matrix.csv")

    exp001 = next(r for r in exp_rows if r["experiment_id"] == "EXP-001")
    exp002 = next(r for r in exp_rows if r["experiment_id"] == "EXP-002")

    upside_001 = float(exp001["estimated_annualized_margin_upside"])
    upside_002 = float(exp002["estimated_annualized_margin_upside"])
    combined   = upside_001 + upside_002

    # Ready to run = High feasibility AND Low launch effort (derived from data)
    ready_count = sum(
        1 for r in exp_rows
        if r["feasibility_rating"] == "High" and r["estimated_launch_effort"] == "Low"
    )

    return [
        {
            "kpi_name":        "EXP-001 Conservative Upside",
            "kpi_value":       round(upside_001, 2),
            "formatted_value": fmt_currency_k(upside_001),
            "sort_order":      1,
        },
        {
            "kpi_name":        "EXP-002 Conservative Upside",
            "kpi_value":       round(upside_002, 2),
            "formatted_value": fmt_currency_k(upside_002),
            "sort_order":      2,
        },
        {
            "kpi_name":        "Combined Ready-to-Run Upside",
            "kpi_value":       round(combined, 2),
            "formatted_value": fmt_currency_k(combined),
            "sort_order":      3,
        },
        {
            "kpi_name":        "Experiments Ready to Run Now",
            "kpi_value":       ready_count,
            "formatted_value": str(ready_count),
            "sort_order":      4,
        },
    ]


# ---------------------------------------------------------------------------
# 6. growth_lever_scorecard.csv  (Tab 3 source - fields trimmed for Tableau)
# ---------------------------------------------------------------------------

# Dropped: impact_period (same value on every row), estimated_margin_uplift
# (cumulative; annualized column is used for all comparisons), assumption_note
# (multi-sentence technical caveat; too long for Tableau cells).
SCORECARD_KEEP = [
    "priority_rank",
    "lever",
    "lever_type",
    "scenario",
    "estimated_margin_uplift_annualized",
    "math_confidence",
    "execution_confidence",
    "feasibility_rating",
    "notes",
]


def _clean(val: str) -> str:
    return (val
            .replace("→", "to")
            .replace("—", "-")
            .replace("–", "-")
            .replace("−", "-"))  # mathematical minus sign


def build_scorecard() -> list[dict]:
    rows = read_csv("growth_lever_scorecard.csv")
    return [{k: _clean(r[k]) for k in SCORECARD_KEEP} for r in rows]


# ---------------------------------------------------------------------------
# 7. experiment_priority_matrix.csv  (Tab 3 source - all fields kept)
# ---------------------------------------------------------------------------

def build_experiment_matrix() -> list[dict]:
    return read_csv("experiment_priority_matrix.csv")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    TABLEAU_DIR.mkdir(parents=True, exist_ok=True)

    print("\nbuild_tableau_exports.py")
    print("=" * 50)

    total  = 0
    total += write_tableau_csv(build_executive_kpis(),    "executive_kpis.csv")
    total += write_tableau_csv(build_waterfall_data(),    "waterfall_data.csv")
    total += write_tableau_csv(build_funnel_summary(),    "funnel_summary.csv")
    total += write_tableau_csv(build_buyer_split(),       "buyer_split.csv")
    total += write_tableau_csv(build_action_plan_kpis(),  "action_plan_kpis.csv")
    total += write_tableau_csv(build_scorecard(),          "growth_lever_scorecard.csv")
    total += write_tableau_csv(build_experiment_matrix(),  "experiment_priority_matrix.csv")

    print("=" * 50)
    print(f"Done. {total} total rows written to outputs/tableau/\n")


if __name__ == "__main__":
    main()
