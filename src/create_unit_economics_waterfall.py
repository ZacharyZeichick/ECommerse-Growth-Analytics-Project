"""
create_unit_economics_waterfall.py

Builds a single waterfall chart: Gross Revenue → Cancellations → Returns →
Estimated Product Cost → Estimated Net Margin.

Sources:
  outputs/tables/post_purchase_summary.csv    — gross, cancelled, returned, net revenue
  outputs/tables/margin_mix_opportunity.csv   — platform_margin_pct (51.9%)

Product cost is estimated: net_revenue × (1 − platform_margin_pct).
The 51.9% margin rate is a weighted average computed from actual product
cost data across all 26 categories.

Output:
  outputs/figures/unit_economics_waterfall.png

Run from the repo root: python src/create_unit_economics_waterfall.py
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

REPO_ROOT   = Path(__file__).parent.parent
TABLES_DIR  = REPO_ROOT / "outputs" / "tables"
FIGURES_DIR = REPO_ROOT / "outputs" / "figures"

FIGURES_DIR.mkdir(parents=True, exist_ok=True)

BLUE      = "#2563EB"
RED_SOFT  = "#F87171"
AMBER     = "#F59E0B"
SLATE     = "#64748B"
GREEN     = "#10B981"
GRID_GRAY = "#E5E7EB"
LABEL_DARK = "#1F2937"


def main() -> None:
    print("\nE-Commerce Growth Analytics - Unit Economics Waterfall")
    print(f"Output: {FIGURES_DIR}")
    print()

    # ------------------------------------------------------------------ #
    # Load data
    # ------------------------------------------------------------------ #
    pp = pd.read_csv(TABLES_DIR / "post_purchase_summary.csv").iloc[0]
    margin_df = pd.read_csv(TABLES_DIR / "margin_mix_opportunity.csv")

    gross         = float(pp["gross_revenue"])
    cancelled     = float(pp["cancelled_revenue"])
    returned      = float(pp["returned_revenue"])
    net_rev       = float(pp["net_revenue"])
    margin_pct    = float(margin_df["platform_margin_pct"].iloc[0]) / 100  # 0.519

    product_cost  = net_rev * (1.0 - margin_pct)
    net_margin    = net_rev * margin_pct

    # ------------------------------------------------------------------ #
    # Waterfall bar definitions
    # (label, bottom, height, color, is_total)
    #
    # Reduction bars are positioned so their top aligns with the current
    # running total and their bottom sits at (running_total − reduction).
    # Total bars sit flush on the x-axis (bottom = 0).
    # ------------------------------------------------------------------ #
    steps = [
        ("Gross\nRevenue",        0,            gross,        BLUE,     True),
        ("Less:\nCancellations",  net_rev + returned, cancelled,    RED_SOFT, False),
        ("Less:\nReturns",        net_rev,      returned,     AMBER,    False),
        ("Less:\nProduct Cost",   net_margin,   product_cost, SLATE,    False),
        ("Estimated\nNet Margin", 0,            net_margin,   GREEN,    True),
    ]

    labels    = [s[0] for s in steps]
    bottoms   = [s[1] for s in steps]
    heights   = [s[2] for s in steps]
    colors    = [s[3] for s in steps]
    is_totals = [s[4] for s in steps]

    fig, ax = plt.subplots(figsize=(12, 7))
    x_pos = range(len(steps))
    bar_width = 0.55

    bars = ax.bar(x_pos, heights, bottom=bottoms, color=colors,
                  width=bar_width, zorder=3)

    # ------------------------------------------------------------------ #
    # Connector lines between bars (horizontal, at transition height)
    # ------------------------------------------------------------------ #
    # Value at the "seam" between each consecutive pair of bars
    connectors = [
        gross,              # top of Gross Revenue = top of Less Cancellations
        net_rev + returned, # bottom of Less Cancellations = top of Less Returns
        net_rev,            # bottom of Less Returns = top of Less Product Cost
        net_margin,         # bottom of Less Product Cost = top of Net Margin
    ]
    half = bar_width / 2
    for i, val in enumerate(connectors):
        ax.plot(
            [i + half, i + 1 - half],
            [val, val],
            color=GRID_GRAY, linewidth=1.4, zorder=2, solid_capstyle="round",
        )

    # ------------------------------------------------------------------ #
    # Value labels inside each bar (white text, vertically centered)
    # ------------------------------------------------------------------ #
    for i, (bottom, height, is_total) in enumerate(zip(bottoms, heights, is_totals)):
        midpoint = bottom + height / 2
        pct_gross = height / gross * 100
        sign = "" if is_total else "−"   # minus sign (−) for reductions
        line1 = f"{sign}${height / 1_000_000:.2f}M"
        line2 = f"({pct_gross:.1f}% of gross)"
        ax.text(
            i, midpoint,
            f"{line1}\n{line2}",
            ha="center", va="center",
            fontsize=9.5 if is_total else 8.5,
            fontweight="bold" if is_total else "normal",
            color="white", zorder=4,
        )

    # ------------------------------------------------------------------ #
    # Running-total annotations (small gray text at connector seam)
    # ------------------------------------------------------------------ #
    # Show intermediate subtotals to the right of the connector line
    subtotals = [
        (0, gross,           ""),                           # Gross Revenue — skip (already labeled)
        (1, net_rev + returned, f"${(net_rev + returned) / 1_000_000:.2f}M"),
        (2, net_rev,         f"${net_rev / 1_000_000:.2f}M  ← net revenue"),
        (3, net_margin,      ""),                           # Net Margin — skip (labeled on bar)
    ]
    for i, val, label in subtotals:
        if label:
            ax.text(
                i + half + 0.05, val + gross * 0.012,
                label,
                ha="left", va="bottom",
                fontsize=8, color="#6B7280", zorder=4,
            )

    # ------------------------------------------------------------------ #
    # Axes, grid, labels
    # ------------------------------------------------------------------ #
    ax.set_xticks(list(x_pos))
    ax.set_xticklabels(labels, fontsize=10.5)
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda v, _: f"${v / 1_000_000:.1f}M")
    )
    ax.set_ylabel("USD (millions)", fontsize=11)
    ax.set_title(
        "Unit Economics Waterfall — Full Dataset Period (2019–2026)\n"
        "Gross Revenue to Estimated Net Margin",
        fontsize=13, pad=14,
    )
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
    ax.set_ylim(0, gross * 1.14)
    ax.set_xlim(-0.55, len(steps) - 0.45)

    # ------------------------------------------------------------------ #
    # Footnote
    # ------------------------------------------------------------------ #
    fig.text(
        0.5, 0.005,
        "Product cost estimated using platform net margin rate of 51.9% "
        "(weighted avg across 26 categories; derived from actual product cost data).",
        ha="center", fontsize=8, color="#9CA3AF",
    )

    plt.tight_layout(rect=[0, 0.03, 1, 1])
    out = FIGURES_DIR / "unit_economics_waterfall.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out.name}")
    print("\nDone.")


if __name__ == "__main__":
    main()
