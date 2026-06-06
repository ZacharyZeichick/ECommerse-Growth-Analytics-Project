"""
build_experiment_recommendations.py

Builds four A/B experiment designs grounded in the prior analysis outputs.
Reads from outputs/tables/ (no DuckDB needed — all inputs are already computed CSVs).
Writes three output CSVs to outputs/tables/.
Run from the repo root: python src/build_experiment_recommendations.py

Source inputs used:
  growth_lever_scorecard.csv       — upside estimates, confidence, feasibility ratings
  recommended_experiments.csv      — top-level experiment scaffolding
  funnel_by_traffic_source.csv     — cart session volumes, channel breakdown
  first_purchase_category_customer_value.csv — repeat buyer rate, LTV by category
  post_purchase_summary.csv        — cancellation rate, return rate, item counts
"""

from pathlib import Path
import csv

REPO_ROOT  = Path(__file__).parent.parent
TABLES_DIR = REPO_ROOT / "outputs" / "tables"

IMPACT_PERIOD = "Full dataset period, 2019-2026"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_csv(filename: str) -> list[dict]:
    with open(TABLES_DIR / filename, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def find_row(rows, **kwargs):
    """Return first row where every kwarg value appears as a substring of that field."""
    for row in rows:
        if all(v in row.get(k, "") for k, v in kwargs.items()):
            return row
    return None


def write_csv(rows: list[dict], filename: str, label: str) -> int:
    print(f"  {label} ...", end=" ", flush=True)
    if not rows:
        print("0 rows  (empty)")
        return 0
    path = TABLES_DIR / filename
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} rows  ->  {path.name}")
    return len(rows)


# ---------------------------------------------------------------------------
# Load inputs and extract key data points
# ---------------------------------------------------------------------------

def load_inputs() -> dict:
    scorecard   = read_csv("growth_lever_scorecard.csv")
    funnel      = read_csv("funnel_by_traffic_source.csv")
    ltv         = read_csv("first_purchase_category_customer_value.csv")
    pp          = read_csv("post_purchase_summary.csv")[0]
    cust        = read_csv("customer_purchase_summary.csv")[0]

    # Funnel aggregates
    total_cart      = sum(int(r["cart_sessions"])     for r in funnel)
    total_purchases = sum(int(r["purchase_sessions"]) for r in funnel)
    non_converting  = total_cart - total_purchases
    c2p_rate        = round(total_purchases / total_cart * 100, 1)
    email_row       = find_row(funnel, traffic_source="Email")
    email_sessions  = int(email_row["sessions"]) if email_row else 0
    email_pct       = round(email_sessions / sum(int(r["sessions"]) for r in funnel) * 100, 1)

    # Post-purchase aggregates
    cancel_rate  = float(pp["cancellation_rate"])
    return_rate  = float(pp["return_rate"])
    total_items  = int(pp["total_items"])
    cancel_items = round(total_items * cancel_rate / 100)

    # Platform repeat buyer rate — weighted, derived from actual buyer counts
    _repeat  = int(cust["repeat_buyers"])
    _total   = _repeat + int(cust["one_time_buyers"])
    avg_repeat_rate = round(_repeat / _total * 100, 1)
    one_time_pct    = round(int(cust["one_time_buyers"]) / _total * 100, 1)

    # Upside values from scorecard — match on lever_type + lever name fragment.
    # Using lever fragments rather than scenario strings to avoid special-character
    # ambiguity (e.g., en dash vs hyphen in "Cancellation rate −1pp").
    # exclude_fragment prevents "1%" from accidentally matching "10%" rows.
    def upside(lever_type, lever_fragment, exclude_fragment=None):
        for row in scorecard:
            if row.get("lever_type", "") != lever_type:
                continue
            lever = row.get("lever", "")
            if lever_fragment not in lever:
                continue
            if exclude_fragment and exclude_fragment in lever:
                continue
            return (
                float(row["estimated_margin_uplift_annualized"]),
                row["math_confidence"],
                row["execution_confidence"],
                row["feasibility_rating"],
            )
        return None, None, None, None

    cart_1pp_ann,    cart_math,  cart_exec,  cart_feas  = upside("Conversion",    "+1pp")
    repeat_5pct_ann, rep_math,   rep_exec,   rep_feas   = upside("Retention",     "+5%")
    cancel_1pp_ann,  can_math,   can_exec,   can_feas   = upside("Post-purchase", "1pp", "3pp")
    mix_1pct_ann,    mix_math,   mix_exec,   mix_feas   = upside("Mix shift",     "1%",  "10%")

    return {
        "total_cart":        total_cart,
        "total_purchases":   total_purchases,
        "non_converting":    non_converting,
        "c2p_rate":          c2p_rate,
        "email_sessions":    email_sessions,
        "email_pct":         email_pct,
        "cancel_rate":       cancel_rate,
        "return_rate":       return_rate,
        "total_items":       total_items,
        "cancel_items":      cancel_items,
        "avg_repeat_rate":   avg_repeat_rate,
        "one_time_pct":      one_time_pct,
        "cart_1pp_ann":      cart_1pp_ann,
        "cart_math":         cart_math,
        "cart_exec":         cart_exec,
        "cart_feas":         cart_feas,
        "repeat_5pct_ann":   repeat_5pct_ann,
        "rep_math":          rep_math,
        "rep_exec":          rep_exec,
        "rep_feas":          rep_feas,
        "cancel_1pp_ann":    cancel_1pp_ann,
        "can_math":          can_math,
        "can_exec":          can_exec,
        "can_feas":          can_feas,
        "mix_1pct_ann":      mix_1pct_ann,
        "mix_math":          mix_math,
        "mix_exec":          mix_exec,
        "mix_feas":          mix_feas,
    }


# ---------------------------------------------------------------------------
# Q1 — Experiment designs
# ---------------------------------------------------------------------------

def build_experiment_designs(d: dict) -> list[dict]:
    return [
        # ------------------------------------------------------------------
        # EXP-001: Cart abandonment recovery
        # Lever: Conversion. Upside: +1pp cart-to-purchase rate scenario.
        # Grounding: {d['non_converting']:,} non-converting cart sessions;
        #            current cart-to-purchase rate {d['c2p_rate']}%.
        # ------------------------------------------------------------------
        {
            "experiment_id":         "EXP-001",
            "experiment_name":       "Cart abandonment recovery",
            "business_lever":        "Conversion (cart-to-purchase rate)",
            "hypothesis": (
                f"Sending a single timed cart-reminder email to registered users who added "
                f"items to cart but did not purchase within 24 hours will recover a "
                f"measurable share of the {d['non_converting']:,} non-converting cart "
                f"sessions per dataset period and lift the cart-to-purchase rate "
                f"(currently {d['c2p_rate']}%) by at least 1pp."
            ),
            "target_segment": (
                "Registered users with an active cart and no purchase event within 24 hours "
                "of their last cart event. Excludes guest sessions (no email address available) "
                "and users who purchased within the same session."
            ),
            "control_experience": (
                "No follow-up communication after cart abandonment — current default behavior."
            ),
            "treatment_experience": (
                "Single cart-reminder email sent 24 hours after the last cart event. "
                "Content: itemized cart summary with product images, direct link back to cart. "
                "No promotional discount in v1 — test urgency and reminder before layering "
                "incentives to isolate the reminder effect."
            ),
            "primary_metric":   "Cart-to-purchase rate (purchases / cart sessions, 7-day window from cart event date)",
            "guardrail_metrics": (
                "Email unsubscribe rate — must not increase by more than 0.5pp vs control; "
                "average order value of recovered purchases — monitor for value dilution vs historical avg; "
                "session purchase rate for non-cart users — confirm no cannibalization of organic demand"
            ),
            "expected_direction": "Increase in cart-to-purchase rate",
            "upside_scenario":    "+1pp cart-to-purchase rate (conservative; 5pp is the high-end scenario)",
            "estimated_annualized_margin_upside": d["cart_1pp_ann"],
            "impact_period":      IMPACT_PERIOD,
            "math_confidence":    d["cart_math"],
            "execution_confidence": "Medium",
            "feasibility_rating": d["cart_feas"],
            "implementation_notes": (
                "Requires: (1) linkage between cart events in the events table and user email "
                "addresses; (2) 24-hour delay trigger in email send infrastructure; (3) "
                "suppression logic to exclude users who purchased after cart abandonment. "
                f"Email already drives {d['email_pct']}% of all sessions — existing channel "
                "infrastructure should be available. Start with no-discount version to "
                "establish baseline lift before testing promotional variants."
            ),
            "risk_caveat": (
                "Upside estimate assumes marginal recovered sessions have average purchase margin "
                "($23.30/session). Non-converting cart sessions may be more price-sensitive "
                "or have lower-value items, so true marginal margin may be lower than average. "
                f"Email fatigue risk: Email already drives {d['email_pct']}% of sessions; "
                "adding abandonment triggers increases send volume on an already-active channel."
            ),
        },

        # ------------------------------------------------------------------
        # EXP-002: One-time buyer reactivation
        # Lever: Retention. Upside: +5% more repeat orders scenario.
        # Grounding: avg repeat buyer rate {d['avg_repeat_rate']}%;
        #            ~{d['one_time_pct']}% of buyers never return.
        # ------------------------------------------------------------------
        {
            "experiment_id":         "EXP-002",
            "experiment_name":       "One-time buyer reactivation",
            "business_lever":        "Retention (repeat purchase rate)",
            "hypothesis": (
                f"A two-touch email sequence sent to customers with exactly one lifetime "
                f"purchase will increase the 90-day repeat order rate, recovering a portion "
                f"of the ~{d['one_time_pct']}% of buyers who never return. "
                f"The current average repeat buyer rate is {d['avg_repeat_rate']}% across "
                f"all first-purchase categories."
            ),
            "target_segment": (
                "Customers with exactly one lifetime purchase, where that purchase was "
                "30 or more days ago (excludes recent buyers who may repurchase naturally). "
                "Excludes customers currently in an active cart session or with a pending order."
            ),
            "control_experience": (
                "No proactive outreach — standard transactional emails only (order confirmation, "
                "shipping updates)."
            ),
            "treatment_experience": (
                "Two-touch email sequence: Touch 1 at day 30 post-purchase — "
                "personalized product recommendations based on first-purchase category "
                "(e.g., Outerwear buyer receives Sweaters and Accessories suggestions). "
                "Touch 2 at day 60 — curated 'Back in Season' or 'Complete the Look' "
                "content with a time-limited offer if Touch 1 generated no purchase."
            ),
            "primary_metric":   "Repeat order rate in the 90-day window following sequence start (orders placed / customers messaged)",
            "guardrail_metrics": (
                "Email unsubscribe rate — must not increase by more than 0.5pp vs control; "
                "margin per re-engaged order — should not fall below historical avg repeat order margin; "
                "revenue per email sent — efficiency guardrail to monitor diminishing returns across cohorts"
            ),
            "expected_direction": "Increase in 90-day repeat order rate vs control",
            "upside_scenario":    "+5% more repeat purchase orders (conservative; 10% is the high-end scenario)",
            "estimated_annualized_margin_upside": d["repeat_5pct_ann"],
            "impact_period":      IMPACT_PERIOD,
            "math_confidence":    d["rep_math"],
            "execution_confidence": d["rep_exec"],
            "feasibility_rating": d["rep_feas"],
            "implementation_notes": (
                "Requires: (1) segmentation query to identify one-time buyers with 30+ day recency; "
                "(2) first-purchase category lookup per customer for personalization; "
                "(3) two-step send logic with purchase-event suppression between touches. "
                "Personalization by first-purchase category is supported by the product value "
                "analysis — each category has a documented avg lifetime margin and repeat rate. "
                "Start with the highest-LTV first-purchase categories (Outerwear & Coats $99 LTM, "
                "Suits & Sport Coats $93 LTM) to maximize expected return per email sent."
            ),
            "risk_caveat": (
                "Repeat buyer rate is flat at ~37-38% across all 26 categories — retention is a "
                "platform-level behavior, not category-driven. Category-personalized messaging "
                "may not meaningfully outperform generic messaging. "
                "Incremental repeat orders from reactivated one-time buyers may have lower average "
                "value than the $65.48 historical repeat order average used in the upside estimate. "
                "The ~63% one-time buyer rate may partially reflect price-sensitive opportunistic "
                "buyers who are unlikely to reactivate regardless of messaging."
            ),
        },

        # ------------------------------------------------------------------
        # EXP-003: High-margin category merchandising test
        # Lever: Mix shift. Upside: 1% mix shift scenario (most achievable).
        # Grounding: Blazers & Jackets 62.1% margin, Accessories 59.9% margin;
        #            platform avg 51.9%; both significantly underscaled.
        # ------------------------------------------------------------------
        {
            "experiment_id":         "EXP-003",
            "experiment_name":       "High-margin category merchandising test",
            "business_lever":        "Product mix (margin mix shift)",
            "hypothesis": (
                "Increasing the search ranking and browse placement visibility of "
                "Blazers & Jackets (62.1% margin, currently underscaled) and Accessories "
                "(59.9% margin) for relevant queries will shift a measurable share of "
                "demand toward higher-margin categories, improving the blended platform "
                "margin percentage without reducing total session purchase rate."
            ),
            "target_segment": (
                "All browsing users — treatment is applied at the search and navigation layer, "
                "not targeted by user segment. Apply to queries and browse contexts where "
                "Blazers & Jackets or Accessories are contextually relevant "
                "(e.g., formal wear, work outfit, layering, gifts)."
            ),
            "control_experience": (
                "Current default search ranking and browse/navigation placement for "
                "Blazers & Jackets and Accessories categories."
            ),
            "treatment_experience": (
                "Elevated search result ranking and browse-page placement for Blazers & Jackets "
                "and Accessories within defined relevant query and browse contexts. "
                "No change to category pages, pricing, or product descriptions."
            ),
            "primary_metric":   "Revenue share of Blazers & Jackets + Accessories (% of total net revenue in the measurement period)",
            "guardrail_metrics": (
                "Overall session purchase rate — must not decline vs control (surfacing "
                "irrelevant products would reduce conversion); "
                "total net revenue — confirm zero-sum or positive shift, not revenue loss; "
                "blended estimated margin pct — confirm directional improvement"
            ),
            "expected_direction": "Increase in high-margin category revenue share; flat or improved blended margin pct",
            "upside_scenario":    "1% revenue shift from low-margin to margin-leader categories (most achievable scenario)",
            "estimated_annualized_margin_upside": d["mix_1pct_ann"],
            "impact_period":      IMPACT_PERIOD,
            "math_confidence":    d["mix_math"],
            "execution_confidence": d["mix_exec"],
            "feasibility_rating": d["mix_feas"],
            "implementation_notes": (
                "Requires access to search ranking and browse placement configuration. "
                "Define 'relevant query contexts' narrowly before launch — avoid surfacing "
                "Blazers to users searching for casual wear, which would reduce conversion "
                "without improving mix. Measure both category traffic lift AND downstream "
                "conversion rate for treated categories to distinguish discovery from purchase intent. "
                "Run for a minimum of 4 weeks to capture weekly seasonality."
            ),
            "risk_caveat": (
                "This is the weakest lever by annualized margin impact — the 1% shift scenario "
                f"yields ~${d['mix_1pct_ann']:,.0f}/yr annualized. Fashion demand is highly "
                "category-sticky; forced exposure to Blazers does not reliably convert Jeans "
                "shoppers. The primary value of this experiment is learning whether demand is "
                "transferable at all, not achieving material margin improvement. "
                "Do not treat the upside estimate as a reliable forecast — it assumes full demand "
                "transferability, which this experiment is designed to test."
            ),
        },

        # ------------------------------------------------------------------
        # EXP-004: Cancellation reason capture and prevention pilot
        # Lever: Post-purchase (cancellation reduction).
        # Upside: -1pp cancellation rate scenario.
        # Grounding: {d['cancel_rate']}% cancel rate, ~{d['cancel_items']:,} cancelled
        #            items per dataset period. Root cause not captured in dataset.
        # Two-phase: Phase A = instrumentation; Phase B = intervention.
        # ------------------------------------------------------------------
        {
            "experiment_id":         "EXP-004",
            "experiment_name":       "Cancellation reason capture and pre-cancellation intervention pilot",
            "business_lever":        "Post-purchase (cancellation rate reduction)",
            "hypothesis": (
                f"The {d['cancel_rate']}% cancellation rate is flat across all categories, "
                f"order values, customer types, and distribution centers — suggesting a "
                f"systematic driver rather than a segment-specific one. Phase A: adding a "
                f"required reason-selection step to the cancellation flow will identify the "
                f"primary cancellation driver. Phase B: surfacing a targeted pre-cancellation "
                f"message for the most common reason (e.g., delivery reassurance for "
                f"delivery-anxiety cancellations) will reduce the cancellation rate by at least 1pp."
            ),
            "target_segment": (
                "Phase A: All users initiating a cancellation (full population). "
                "Phase B: Users initiating a cancellation who trigger the pre-defined "
                "intervention condition (e.g., 'delivery timing' reason selected). "
                "Phase B segment size is unknown until Phase A reason data is collected."
            ),
            "control_experience": (
                "Current cancellation flow: user confirms cancellation with no reason capture "
                "and no pre-cancellation messaging."
            ),
            "treatment_experience": (
                "Phase A: Cancellation flow with a required single-select reason field "
                "(taxonomy: delivery timing / price or found better deal / changed mind / "
                "ordering error / other). No intervention — pure instrumentation. "
                "Phase B (design after Phase A): Targeted pre-cancellation message shown "
                "before confirmation for the highest-volume reason. "
                "Example for delivery timing: 'Your order ships within X days — want to keep it?'"
            ),
            "primary_metric":   "Cancellation rate (cancelled items / total items ordered in the measurement period)",
            "guardrail_metrics": (
                "Cancellation flow completion time — must not increase materially vs control "
                "(adding friction to cancellation risks damaging trust and NPS); "
                "return rate on orders that did not cancel after seeing Phase B message — "
                "ensure prevented cancellations do not convert to returns instead; "
                "customer contact rate (support tickets) — monitor for frustration signal"
            ),
            "expected_direction": "Phase A: No change in cancellation rate (instrumentation only). Phase B: Decrease in cancellation rate",
            "upside_scenario":    "-1pp cancellation rate (most achievable scenario; requires Phase A to validate intervention design)",
            "estimated_annualized_margin_upside": d["cancel_1pp_ann"],
            "impact_period":      IMPACT_PERIOD,
            "math_confidence":    d["can_math"],
            "execution_confidence": "Low",
            "feasibility_rating": d["can_feas"],
            "implementation_notes": (
                "Phase A is low engineering effort — a single required form field added to the "
                "cancellation confirmation screen. Run Phase A for a minimum of 4 weeks to "
                "collect statistically meaningful reason distribution. "
                "Phase B design is entirely dependent on Phase A findings — do not design "
                "the intervention before the reason data is available. "
                "Phase B should be a proper A/B test: random assignment within the "
                "intervention-eligible segment (users who selected the target reason)."
            ),
            "risk_caveat": (
                "Execution confidence is Low because the root cause is unknown. "
                "If the dominant cancellation reason is 'changed mind' or 'found better deal', "
                "a pre-cancellation message is unlikely to recover the order and may damage "
                "trust by appearing to obstruct cancellation. "
                "The upside estimate ($7,638/yr annualized for -1pp) assumes recovered items "
                "complete at the average margin of cancelled items ($31.11/item) and does not "
                "account for fulfillment costs already incurred at the point of cancellation. "
                "Phase A result is the primary deliverable — the cancellation rate reduction "
                "is a secondary outcome contingent on Phase A findings."
            ),
        },
    ]


# ---------------------------------------------------------------------------
# Q2 — Experiment priority matrix
# ---------------------------------------------------------------------------

def build_priority_matrix(designs: list[dict]) -> list[dict]:
    # recommended_launch_order reflects practical sequencing:
    # EXP-001 and EXP-002 share email infrastructure and can run in parallel.
    # EXP-004 Phase A is low-cost instrumentation and should run early.
    # EXP-003 requires search system access and has the lowest ROI — run last.
    recommended_order = {
        "EXP-001": 1,   # Highest upside, high feasibility, email infrastructure ready
        "EXP-002": 2,   # Parallel with EXP-001, same channel, high feasibility
        "EXP-004": 3,   # Phase A is pure instrumentation, low effort, fills critical data gap
        "EXP-003": 4,   # Requires search system access; run last — learning value > margin impact
    }
    launch_rationale = {
        "EXP-001": "Highest annualized upside; email infrastructure likely shared with EXP-002; can run in parallel",
        "EXP-002": "High feasibility; runs on same email channel as EXP-001; medium upside",
        "EXP-004": "Phase A is low-effort instrumentation that fills a critical data gap before any post-purchase intervention is designed",
        "EXP-003": "Lowest annualized upside; requires search system changes; primary value is learning about demand elasticity",
    }
    learning_value = {
        "EXP-001": "Medium",  # Confirms if cart reminder works; does not explain abandonment reason
        "EXP-002": "Medium",  # Confirms if one-time buyers can be reactivated; tests personalization
        "EXP-003": "High",    # Tests whether fashion demand is transferable — answers a fundamental mix-shift question
        "EXP-004": "High",    # Phase A fills the biggest data gap in the analysis; enables all future post-purchase work
    }
    launch_effort = {
        "EXP-001": "Low",     # Email trigger + suppression logic
        "EXP-002": "Low",     # Email sequence + segmentation query
        "EXP-003": "Medium",  # Search ranking configuration changes
        "EXP-004": "Low",     # Phase A: single form field addition to cancel flow
    }

    rows = []
    for d in designs:
        eid = d["experiment_id"]
        rows.append({
            "recommended_launch_order":           recommended_order[eid],
            "experiment_id":                      eid,
            "experiment_name":                    d["experiment_name"],
            "business_lever":                     d["business_lever"],
            "estimated_annualized_margin_upside": d["estimated_annualized_margin_upside"],
            "upside_scenario":                    d["upside_scenario"],
            "math_confidence":                    d["math_confidence"],
            "execution_confidence":               d["execution_confidence"],
            "feasibility_rating":                 d["feasibility_rating"],
            "estimated_launch_effort":            launch_effort[eid],
            "learning_value":                     learning_value[eid],
            "launch_rationale":                   launch_rationale[eid],
        })

    rows.sort(key=lambda r: r["recommended_launch_order"])
    return rows


# ---------------------------------------------------------------------------
# Q3 — Experiment metric definitions
# ---------------------------------------------------------------------------

def build_metric_definitions() -> list[dict]:
    return [
        # Primary metrics
        {
            "metric_id":          "M-001",
            "metric_name":        "Cart-to-purchase rate",
            "metric_type":        "Primary",
            "definition":         "Count of sessions with a purchase event divided by count of sessions with a cart event, measured within a 7-day window from the cart event date.",
            "measurement_window": "7 days from cart event date",
            "data_source":        "events table (event_type IN ('cart','purchase')); existing in data/processed/events.csv",
            "experiment_ids":     "EXP-001",
        },
        {
            "metric_id":          "M-002",
            "metric_name":        "Repeat order rate (90-day)",
            "metric_type":        "Primary",
            "definition":         "Proportion of targeted one-time buyers who place at least one additional order within 90 days of the sequence start date.",
            "measurement_window": "90 days from email sequence start date",
            "data_source":        "orders table; requires join to campaign send log (new instrumentation needed)",
            "experiment_ids":     "EXP-002",
        },
        {
            "metric_id":          "M-003",
            "metric_name":        "High-margin category revenue share",
            "metric_type":        "Primary",
            "definition":         "Net revenue from Blazers & Jackets and Accessories combined, divided by total platform net revenue, in the measurement period.",
            "measurement_window": "4-week test period (minimum)",
            "data_source":        "order_items + products tables; existing in data/processed/",
            "experiment_ids":     "EXP-003",
        },
        {
            "metric_id":          "M-004",
            "metric_name":        "Cancellation rate",
            "metric_type":        "Primary",
            "definition":         "Count of order items with status='Cancelled' divided by total order items created in the measurement period.",
            "measurement_window": "Duration of test; allow 2 weeks minimum for signal to stabilize",
            "data_source":        "order_items table; existing in data/processed/order_items.csv",
            "experiment_ids":     "EXP-004",
        },
        # Guardrail metrics
        {
            "metric_id":          "M-005",
            "metric_name":        "Email unsubscribe rate",
            "metric_type":        "Guardrail",
            "definition":         "Count of unsubscribe events divided by count of emails sent, per campaign send. Alert threshold: increase of more than 0.5pp vs control group rate.",
            "measurement_window": "Per email send; cumulative over test period",
            "data_source":        "Email send platform (new instrumentation; not in current dataset)",
            "experiment_ids":     "EXP-001, EXP-002",
        },
        {
            "metric_id":          "M-006",
            "metric_name":        "Average order value of recovered purchases",
            "metric_type":        "Guardrail",
            "definition":         "Mean sale_price per order for purchases attributable to the experiment treatment (recovered cart sessions or reactivated buyers). Monitor for value dilution vs historical avg.",
            "measurement_window": "Same as primary metric window",
            "data_source":        "order_items table + experiment assignment log",
            "experiment_ids":     "EXP-001, EXP-002",
        },
        {
            "metric_id":          "M-007",
            "metric_name":        "Overall session purchase rate",
            "metric_type":        "Guardrail",
            "definition":         "Count of sessions with a purchase event divided by total sessions, across all users (not just treatment group). Detects cannibalization of organic demand.",
            "measurement_window": "Same as primary metric window",
            "data_source":        "events table; existing in data/processed/events.csv",
            "experiment_ids":     "EXP-001, EXP-003",
        },
        {
            "metric_id":          "M-008",
            "metric_name":        "Margin per re-engaged order",
            "metric_type":        "Guardrail",
            "definition":         "Estimated net margin (sale_price - product cost) per order placed by a reactivated one-time buyer in the 90-day window. Should not fall materially below historical repeat order margin (~$33.98).",
            "measurement_window": "90 days from sequence start",
            "data_source":        "order_items + products tables; existing in data/processed/",
            "experiment_ids":     "EXP-002",
        },
        {
            "metric_id":          "M-009",
            "metric_name":        "Revenue per email sent",
            "metric_type":        "Guardrail",
            "definition":         "Total net revenue attributable to the email sequence divided by total emails sent. Efficiency guardrail — detects diminishing returns across cohorts.",
            "measurement_window": "Per cohort (30-day send batches recommended)",
            "data_source":        "Email send platform + order_items table (requires attribution window)",
            "experiment_ids":     "EXP-002",
        },
        {
            "metric_id":          "M-010",
            "metric_name":        "Total net revenue",
            "metric_type":        "Guardrail",
            "definition":         "Sum of sale_price for order items with status NOT IN ('Cancelled','Returned') in the measurement period. Confirms mix shift is zero-sum or positive, not revenue-dilutive.",
            "measurement_window": "4-week test period",
            "data_source":        "order_items table; existing in data/processed/order_items.csv",
            "experiment_ids":     "EXP-003",
        },
        {
            "metric_id":          "M-011",
            "metric_name":        "Blended estimated margin pct",
            "metric_type":        "Guardrail",
            "definition":         "Total estimated net margin (SUM(sale_price - cost) for non-cancelled/returned items) divided by total net revenue in the measurement period. Confirms directional improvement from mix shift.",
            "measurement_window": "4-week test period",
            "data_source":        "order_items + products tables; existing in data/processed/",
            "experiment_ids":     "EXP-003",
        },
        {
            "metric_id":          "M-012",
            "metric_name":        "Return rate on non-cancelled orders (post-intervention)",
            "metric_type":        "Guardrail",
            "definition":         "Return rate for orders where cancellation was initiated but not completed (i.e., the pre-cancellation intervention succeeded). Detects substitution of returns for prevented cancellations.",
            "measurement_window": "60 days from order date (allows time for returns to materialize)",
            "data_source":        "order_items table; requires tagging of intervention-recovered orders",
            "experiment_ids":     "EXP-004",
        },
        {
            "metric_id":          "M-013",
            "metric_name":        "Customer contact rate",
            "metric_type":        "Guardrail",
            "definition":         "Rate of support contacts (email, chat, or call) per 1,000 users who encountered the cancellation flow, in the test period. Detects frustration signal from added friction.",
            "measurement_window": "Same as primary metric window",
            "data_source":        "Customer support platform (new instrumentation; not in current dataset)",
            "experiment_ids":     "EXP-004",
        },
    ]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    print("\nE-Commerce Growth Analytics - Experiment Recommendations")
    print(f"Input:  {TABLES_DIR}")
    print(f"Output: {TABLES_DIR}")
    print("\nLoading inputs and building experiment designs:\n")

    d = load_inputs()

    # Print key data points used to ground the designs
    print(f"  Baselines loaded:")
    print(f"    Cart sessions: {d['total_cart']:,} total, {d['non_converting']:,} non-converting ({d['c2p_rate']}% c2p rate)")
    print(f"    Cancellation rate: {d['cancel_rate']}% ({d['cancel_items']:,} items)")
    print(f"    Avg repeat buyer rate: {d['avg_repeat_rate']}% ({d['one_time_pct']}% one-time buyers)")
    print(f"    Annualized upside: cart +1pp=${d['cart_1pp_ann']:,}, repeat +5%=${d['repeat_5pct_ann']:,}, cancel -1pp=${d['cancel_1pp_ann']:,}, mix 1%=${d['mix_1pct_ann']:,}")
    print()

    designs   = build_experiment_designs(d)
    matrix    = build_priority_matrix(designs)
    metrics   = build_metric_definitions()

    total_rows = 0
    total_rows += write_csv(designs,  "experiment_designs.csv",           "Experiment designs")
    total_rows += write_csv(matrix,   "experiment_priority_matrix.csv",   "Experiment priority matrix")
    total_rows += write_csv(metrics,  "experiment_metric_definitions.csv","Experiment metric definitions")

    print(f"\nDone. 3 files written, {total_rows:,} total rows.")


if __name__ == "__main__":
    main()
