"""
create_post_purchase_charts.py

Reads post-purchase CSVs from outputs/tables/ and writes three PNG charts
to outputs/figures/.
Run from the repo root: python src/create_post_purchase_charts.py
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

REPO_ROOT   = Path(__file__).parent.parent
TABLES_DIR  = REPO_ROOT / "outputs" / "tables"
FIGURES_DIR = REPO_ROOT / "outputs" / "figures"

FIGURES_DIR.mkdir(parents=True, exist_ok=True)

BLUE       = "#2563EB"
BLUE_MID   = "#60A5FA"
BLUE_LIGHT = "#BFDBFE"
GRAY       = "#9CA3AF"
RED_SOFT   = "#F87171"
AMBER      = "#F59E0B"


# ---------------------------------------------------------------------------
# Chart 1 — Stacked bar: gross revenue split into net, cancelled, returned
#           Single bar showing the three components of total gross revenue
# ---------------------------------------------------------------------------

def chart_revenue_loss_breakdown() -> None:
    row = pd.read_csv(TABLES_DIR / "post_purchase_summary.csv").iloc[0]

    net_rev    = float(row["net_revenue"])
    cancelled  = float(row["cancelled_revenue"])
    returned   = float(row["returned_revenue"])
    gross      = float(row["gross_revenue"])

    segments = [
        ("Net Revenue",        net_rev,   BLUE),
        ("Cancelled Revenue",  cancelled, RED_SOFT),
        ("Returned Revenue",   returned,  AMBER),
    ]

    fig, ax = plt.subplots(figsize=(7, 7))

    bottom = 0.0
    for label, value, color in segments:
        ax.bar(0, value, bottom=bottom, color=color, width=0.45, zorder=3, label=label)
        pct = value / gross * 100
        ax.text(
            0,
            bottom + value / 2,
            f"${value / 1_000_000:.2f}M\n({pct:.1f}%)",
            ha="center", va="center",
            fontsize=11, fontweight="bold", color="white",
        )
        bottom += value

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v / 1_000_000:.1f}M"))
    ax.set_xlim(-0.5, 0.5)
    ax.set_xticks([])
    ax.set_ylabel("Revenue", fontsize=11)
    ax.set_title(
        "Gross Revenue Breakdown\nNet Revenue vs. Post-Purchase Loss",
        fontsize=12, pad=12,
    )
    ax.legend(fontsize=10, loc="upper right", bbox_to_anchor=(1.35, 1.0))
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.35, zorder=0)
    ax.set_ylim(0, gross * 1.08)

    plt.tight_layout()
    out = FIGURES_DIR / "post_purchase_revenue_loss_breakdown.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out.name}")


# ---------------------------------------------------------------------------
# Chart 2 — Horizontal grouped bar: cancel and return rates, top 10 categories
#           Categories sorted by gross revenue descending (largest at top)
#           Mean reference lines show platform-level rate for context
# ---------------------------------------------------------------------------

def chart_rates_by_category() -> None:
    df = pd.read_csv(TABLES_DIR / "post_purchase_by_category.csv")
    top10 = df.nlargest(10, "gross_revenue").sort_values("gross_revenue", ascending=True)

    categories = top10["category"].tolist()
    cancel_rates = top10["cancellation_rate"].tolist()
    return_rates = top10["return_rate"].tolist()

    y = np.arange(len(categories))
    height = 0.35

    # Platform-level averages from the summary file
    summary = pd.read_csv(TABLES_DIR / "post_purchase_summary.csv").iloc[0]
    avg_cancel = float(summary["cancellation_rate"])
    avg_return = float(summary["return_rate"])

    fig, ax = plt.subplots(figsize=(11, 7))

    b1 = ax.barh(y + height / 2, cancel_rates, height, label="Cancellation rate", color=RED_SOFT, zorder=3)
    b2 = ax.barh(y - height / 2, return_rates,  height, label="Return rate",       color=BLUE_MID, zorder=3)

    # Value labels at end of each bar
    for bar in b1:
        ax.text(
            bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
            f"{bar.get_width():.1f}%",
            va="center", ha="left", fontsize=8, color="#374151",
        )
    for bar in b2:
        ax.text(
            bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
            f"{bar.get_width():.1f}%",
            va="center", ha="left", fontsize=8, color="#374151",
        )

    # Platform average reference lines
    ax.axvline(avg_cancel, linestyle="--", color=RED_SOFT, linewidth=1.2, alpha=0.7,
               label=f"Avg cancellation ({avg_cancel:.1f}%)")
    ax.axvline(avg_return,  linestyle="--", color=BLUE_MID, linewidth=1.2, alpha=0.7,
               label=f"Avg return ({avg_return:.1f}%)")

    ax.set_yticks(y)
    ax.set_yticklabels(categories, fontsize=9)
    ax.set_xlabel("Rate (%)", fontsize=11)
    ax.set_title(
        "Post-Purchase Loss Rates — Top 10 Categories by Gross Revenue\nDashed lines show platform average",
        fontsize=12, pad=12,
    )
    ax.legend(fontsize=9, loc="lower right")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", linestyle="--", alpha=0.35, zorder=0)
    ax.set_xlim(0, max(max(cancel_rates), max(return_rates)) * 1.2)

    plt.tight_layout()
    out = FIGURES_DIR / "post_purchase_rates_by_category.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out.name}")


# ---------------------------------------------------------------------------
# Chart 3 — Grouped bar: cancel and return rates by order value band
#           Four bands in ascending order; shows rates are flat across band
# ---------------------------------------------------------------------------

def chart_loss_by_order_value() -> None:
    df = pd.read_csv(TABLES_DIR / "post_purchase_by_order_value.csv")
    # CSV is already sorted by band_sort (ascending order value)

    bands        = df["order_value_band"].tolist()
    cancel_rates = df["cancellation_rate"].tolist()
    return_rates = df["return_rate"].tolist()

    x = np.arange(len(bands))
    width = 0.35

    # Platform-level averages from the summary file
    summary = pd.read_csv(TABLES_DIR / "post_purchase_summary.csv").iloc[0]
    avg_cancel = float(summary["cancellation_rate"])
    avg_return = float(summary["return_rate"])

    fig, ax = plt.subplots(figsize=(10, 6))

    b1 = ax.bar(x - width / 2, cancel_rates, width, label="Cancellation rate", color=RED_SOFT, zorder=3)
    b2 = ax.bar(x + width / 2, return_rates,  width, label="Return rate",       color=BLUE_MID, zorder=3)

    # Value labels on top of each bar
    for bars in (b1, b2):
        for bar in bars:
            h = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                h + 0.15,
                f"{h:.1f}%",
                ha="center", va="bottom", fontsize=9, color="#374151",
            )

    # Platform average reference lines
    ax.axhline(avg_cancel, linestyle="--", color=RED_SOFT, linewidth=1.2, alpha=0.7,
               label=f"Avg cancellation ({avg_cancel:.1f}%)")
    ax.axhline(avg_return,  linestyle="--", color=BLUE_MID, linewidth=1.2, alpha=0.7,
               label=f"Avg return ({avg_return:.1f}%)")

    # Escape $ so matplotlib mathtext doesn't swallow the dollar signs
    safe_bands = [b.replace("$", r"\$") for b in bands]
    ax.set_xticks(x)
    ax.set_xticklabels(safe_bands, fontsize=11)
    ax.set_ylabel("Rate (%)", fontsize=11)
    ax.set_title(
        "Post-Purchase Loss Rates by Order Value Band\nDashed lines show platform average",
        fontsize=12, pad=12,
    )
    ax.legend(fontsize=9, loc="upper right")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.35, zorder=0)
    ax.set_ylim(0, max(max(cancel_rates), max(return_rates)) * 1.35)

    plt.tight_layout()
    out = FIGURES_DIR / "post_purchase_loss_by_order_value.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out.name}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("\nE-Commerce Growth Analytics - Post-Purchase Charts")
    print(f"Input:  {TABLES_DIR}")
    print(f"Output: {FIGURES_DIR}")
    print()

    print("Generating charts:")
    chart_revenue_loss_breakdown()
    chart_rates_by_category()
    chart_loss_by_order_value()

    print(f"\nDone. 3 charts written to {FIGURES_DIR.name}/")


if __name__ == "__main__":
    main()
