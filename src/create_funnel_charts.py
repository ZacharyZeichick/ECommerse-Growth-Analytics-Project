"""
create_funnel_charts.py

Reads funnel CSVs from outputs/tables/ and writes three PNG charts
to outputs/figures/.
Run from the repo root: python src/create_funnel_charts.py
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


# ---------------------------------------------------------------------------
# Chart 1 — Grouped bar: funnel stage volumes by traffic source
#           Sessions, cart sessions, purchase sessions per channel
# ---------------------------------------------------------------------------

def chart_funnel_volumes() -> None:
    df = pd.read_csv(TABLES_DIR / "funnel_by_traffic_source.csv")
    df = df.sort_values("sessions", ascending=False).reset_index(drop=True)

    sources = df["traffic_source"].tolist()
    x = np.arange(len(sources))
    width = 0.26

    fig, ax = plt.subplots(figsize=(12, 6))

    b1 = ax.bar(x - width,     df["sessions"],          width, label="Total sessions",    color=BLUE,       zorder=3)
    b2 = ax.bar(x,             df["cart_sessions"],      width, label="Added to cart",      color=BLUE_MID,   zorder=3)
    b3 = ax.bar(x + width,     df["purchase_sessions"],  width, label="Purchased",          color=BLUE_LIGHT, zorder=3)

    # Value labels on top of each bar (K abbreviation)
    for bars in (b1, b2, b3):
        for bar in bars:
            h = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                h + 1500,
                f"{h / 1_000:.0f}K",
                ha="center", va="bottom", fontsize=8, color="#374151",
            )

    ax.set_xticks(x)
    ax.set_xticklabels(sources, fontsize=10)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v / 1_000:.0f}K"))
    ax.set_ylabel("Sessions", fontsize=11)
    ax.set_title(
        "Funnel Stage Volumes by Traffic Source\nSessions → Cart → Purchase",
        fontsize=12, pad=12,
    )
    ax.legend(fontsize=9, loc="upper right")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.35, zorder=0)
    ax.set_ylim(0, df["sessions"].max() * 1.18)

    plt.tight_layout()
    out = FIGURES_DIR / "funnel_stage_volumes_by_source.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out.name}")


# ---------------------------------------------------------------------------
# Chart 2 — Grouped bar: conversion rates by traffic source
#           Browse-to-cart rate and cart-to-purchase rate — shows flat finding
# ---------------------------------------------------------------------------

def chart_conversion_rates_by_source() -> None:
    df = pd.read_csv(TABLES_DIR / "funnel_by_traffic_source.csv")
    df = df.sort_values("sessions", ascending=False).reset_index(drop=True)

    sources = df["traffic_source"].tolist()
    x = np.arange(len(sources))
    width = 0.35

    fig, ax = plt.subplots(figsize=(11, 6))

    b1 = ax.bar(x - width / 2, df["browse_to_cart_rate"],   width, label="Browse → Cart rate (%)",    color=BLUE_MID, zorder=3)
    b2 = ax.bar(x + width / 2, df["cart_to_purchase_rate"],  width, label="Cart → Purchase rate (%)",  color=BLUE,     zorder=3)

    # Value labels
    for bars in (b1, b2):
        for bar in bars:
            h = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                h + 0.3,
                f"{h:.1f}%",
                ha="center", va="bottom", fontsize=9, color="#374151",
            )

    # Mean reference lines
    mean_b2c = df["browse_to_cart_rate"].mean()
    mean_c2p = df["cart_to_purchase_rate"].mean()
    ax.axhline(mean_b2c, linestyle="--", color=BLUE_MID, linewidth=1.2, alpha=0.7,
               label=f"Avg browse→cart ({mean_b2c:.1f}%)")
    ax.axhline(mean_c2p, linestyle="--", color=BLUE,     linewidth=1.2, alpha=0.7,
               label=f"Avg cart→purchase ({mean_c2p:.1f}%)")

    ax.set_xticks(x)
    ax.set_xticklabels(sources, fontsize=10)
    ax.set_ylabel("Conversion Rate (%)", fontsize=11)
    ax.set_ylim(0, 85)
    ax.set_title(
        "Conversion Rates by Traffic Source\nFlat funnel performance across all channels",
        fontsize=12, pad=12,
    )
    ax.legend(fontsize=9, loc="upper right")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.35, zorder=0)

    plt.tight_layout()
    out = FIGURES_DIR / "conversion_rates_by_source.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out.name}")


# ---------------------------------------------------------------------------
# Chart 3 — Annotated waterfall: overall funnel drop-off
#           Sessions → cart → purchase with drop counts and rates labeled
# ---------------------------------------------------------------------------

def chart_funnel_waterfall() -> None:
    summary = pd.read_csv(TABLES_DIR / "session_purchase_summary.csv").iloc[0]
    funnel  = pd.read_csv(TABLES_DIR / "funnel_by_traffic_source.csv")

    total_sessions  = int(summary["total_sessions"])
    cart_sessions   = int(funnel["cart_sessions"].sum())
    purchase_sessions = int(summary["purchasing_sessions"])

    stages  = ["All sessions", "Added to cart", "Purchased"]
    counts  = [total_sessions, cart_sessions, purchase_sessions]
    colors  = [BLUE, BLUE_MID, BLUE_LIGHT]

    cart_drop     = total_sessions - cart_sessions
    purchase_drop = cart_sessions - purchase_sessions
    cart_drop_pct     = cart_drop     / total_sessions * 100
    purchase_drop_pct = purchase_drop / cart_sessions  * 100

    fig, ax = plt.subplots(figsize=(9, 6))

    bars = ax.bar(stages, counts, color=colors, width=0.5, zorder=3)

    # Count labels inside bars
    for bar, count in zip(bars, counts):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() / 2,
            f"{count:,.0f}",
            ha="center", va="center",
            fontsize=11, fontweight="bold", color="white",
        )

    # Drop annotations between bars
    ax.annotate(
        f"−{cart_drop:,.0f} sessions\n({cart_drop_pct:.1f}% never add to cart)",
        xy=(0.5, (counts[0] + counts[1]) / 2),
        fontsize=9, ha="center", color=RED_SOFT,
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=RED_SOFT, lw=0.8),
    )
    ax.annotate(
        f"−{purchase_drop:,.0f} sessions\n({purchase_drop_pct:.1f}% abandon cart)",
        xy=(1.5, (counts[1] + counts[2]) / 2),
        fontsize=9, ha="center", color=RED_SOFT,
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=RED_SOFT, lw=0.8),
    )

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v / 1_000:.0f}K"))
    ax.set_ylabel("Sessions", fontsize=11)
    ax.set_title(
        "Overall Purchase Funnel — Session Drop-Off\nCart abandonment is the primary conversion leak",
        fontsize=12, pad=12,
    )
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.35, zorder=0)
    ax.set_ylim(0, total_sessions * 1.15)

    plt.tight_layout()
    out = FIGURES_DIR / "funnel_overall_waterfall.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out.name}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("\nE-Commerce Growth Analytics - Funnel Charts")
    print(f"Input:  {TABLES_DIR}")
    print(f"Output: {FIGURES_DIR}")
    print()

    print("Generating charts:")
    chart_funnel_volumes()
    chart_conversion_rates_by_source()
    chart_funnel_waterfall()

    print(f"\nDone. 3 charts written to {FIGURES_DIR.name}/")


if __name__ == "__main__":
    main()
