"""
create_product_value_charts.py

Reads product value CSVs from outputs/tables/ and writes four PNG charts
to outputs/figures/.
Run from the repo root: python src/create_product_value_charts.py
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

REPO_ROOT   = Path(__file__).parent.parent
TABLES_DIR  = REPO_ROOT / "outputs" / "tables"
FIGURES_DIR = REPO_ROOT / "outputs" / "figures"

FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------

ROLE_COLORS = {
    "Revenue leader":                  "#2563EB",   # blue
    "Low-margin volume category":      "#F59E0B",   # amber
    "Margin leader":                   "#10B981",   # green
    "High-value acquisition category": "#8B5CF6",   # purple
    "Niche category":                  "#9CA3AF",   # gray
}

ROLE_ORDER = [
    "Revenue leader",
    "Low-margin volume category",
    "Margin leader",
    "High-value acquisition category",
    "Niche category",
]

# Short labels used on bar chart x-axis
ROLE_SHORT = {
    "Revenue leader":                  "Revenue\nleader",
    "Low-margin volume category":      "Low-margin\nvolume",
    "Margin leader":                   "Margin\nleader",
    "High-value acquisition category": "High-value\nacquisition",
    "Niche category":                  "Niche",
}


# ---------------------------------------------------------------------------
# Chart 1 — Stacked horizontal bar: first vs post-first order margin
#           Top 10 first-purchase categories by avg total_lifetime_margin
# ---------------------------------------------------------------------------

def chart_first_vs_post() -> None:
    df = pd.read_csv(TABLES_DIR / "first_vs_post_first_order_value.csv")

    top10 = (
        df.nlargest(10, "total_lifetime_margin")
          .sort_values("total_lifetime_margin", ascending=True)   # ascending so highest is at chart top
    )

    fig, ax = plt.subplots(figsize=(11, 7))

    ax.barh(
        range(len(top10)),
        top10["first_order_margin"].values,
        color="#2563EB",
        label="First order",
        height=0.6,
    )
    ax.barh(
        range(len(top10)),
        top10["post_first_order_margin"].values,
        left=top10["first_order_margin"].values,
        color="#93C5FD",
        label="Post-first orders",
        height=0.6,
    )

    # Total label at the right end of each bar
    for i, (_, row) in enumerate(top10.iterrows()):
        ax.text(
            row["total_lifetime_margin"] + 0.8,
            i,
            f'${row["total_lifetime_margin"]:.0f}',
            va="center",
            fontsize=9,
            color="#374151",
        )

    ax.set_yticks(range(len(top10)))
    ax.set_yticklabels(top10["first_purchase_category"].values, fontsize=9)
    ax.set_xlabel("Avg margin per customer ($)", fontsize=10)
    ax.set_title(
        "First vs Post-First Order Margin by First-Purchase Category\n"
        "Top 10 by Avg Lifetime Margin",
        fontsize=12, pad=12,
    )
    ax.set_xlim(0, top10["total_lifetime_margin"].max() * 1.2)
    ax.legend(loc="lower right", fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    out = FIGURES_DIR / "first_vs_post_first_order_margin.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out.name}")


# ---------------------------------------------------------------------------
# Chart 2 — Scatter: avg lifetime margin vs repeat buyer rate
#           All 26 first-purchase categories
# ---------------------------------------------------------------------------

def chart_lifetime_margin_vs_repeat() -> None:
    df = pd.read_csv(TABLES_DIR / "first_purchase_category_customer_value.csv")

    fig, ax = plt.subplots(figsize=(11, 8))

    ax.scatter(
        df["repeat_buyer_rate"],
        df["avg_lifetime_margin"],
        s=70,
        color="#2563EB",
        zorder=3,
        edgecolors="white",
        linewidths=0.5,
    )

    # Mean reference lines — computed first so annotation offsets can use them
    mean_rr = df["repeat_buyer_rate"].mean()
    mean_lm = df["avg_lifetime_margin"].mean()

    for _, row in df.iterrows():
        dx = 5 if row["repeat_buyer_rate"] >= mean_rr else -5
        dy = 4 if row["avg_lifetime_margin"] >= mean_lm else -4
        ax.annotate(
            row["first_purchase_category"],
            xy=(row["repeat_buyer_rate"], row["avg_lifetime_margin"]),
            xytext=(dx, dy),
            textcoords="offset points",
            fontsize=7,
            color="#374151",
            ha="left" if dx > 0 else "right",
        )
    ax.axvline(mean_rr, linestyle="--", color="#9CA3AF", linewidth=1, label=f"Mean category repeat rate ({mean_rr:.1f}%)")
    ax.axhline(mean_lm, linestyle="--", color="#6B7280", linewidth=1, label=f"Mean lifetime margin (${mean_lm:.0f})")

    # Expand x-axis so compressed repeat-rate range is readable
    rr_min, rr_max = df["repeat_buyer_rate"].min(), df["repeat_buyer_rate"].max()
    ax.set_xlim(rr_min - 1.5, rr_max + 1.5)

    ax.set_xlabel("Repeat Buyer Rate (%)", fontsize=11)
    ax.set_ylabel("Avg Lifetime Margin per Customer ($)", fontsize=11)
    ax.set_title(
        "Lifetime Margin vs Repeat Rate by First-Purchase Category",
        fontsize=12, pad=12,
    )
    ax.legend(fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    out = FIGURES_DIR / "lifetime_margin_vs_repeat_rate.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out.name}")


# ---------------------------------------------------------------------------
# Chart 3 — Quadrant scatter: net revenue vs margin %, sized by buyers
#           Colored by strategic role; reference lines at category averages
# ---------------------------------------------------------------------------

def chart_revenue_margin_quadrant() -> None:
    df_q     = pd.read_csv(TABLES_DIR / "product_revenue_margin_quadrant.csv")
    df_roles = pd.read_csv(TABLES_DIR / "product_category_recommendations.csv")

    # Attach strategic role to quadrant data
    df = df_q.merge(df_roles[["category", "strategic_role"]], on="category", how="left")

    avg_rev    = df["net_revenue"].mean()
    avg_margin = df["estimated_net_margin_pct"].mean()

    # Scale bubble sizes linearly into [60, 900] range
    buyers_min = df["buyers"].min()
    buyers_max = df["buyers"].max()
    sizes = 60 + 840 * (df["buyers"] - buyers_min) / (buyers_max - buyers_min)

    fig, ax = plt.subplots(figsize=(13, 9))

    for role in ROLE_ORDER:
        mask = df["strategic_role"] == role
        if not mask.any():
            continue
        ax.scatter(
            df.loc[mask, "net_revenue"],
            df.loc[mask, "estimated_net_margin_pct"],
            s=sizes[mask],
            color=ROLE_COLORS[role],
            alpha=0.78,
            label=role,
            zorder=3,
            edgecolors="white",
            linewidths=0.5,
        )

    # Reference lines
    ax.axvline(avg_rev,    linestyle="--", color="#9CA3AF", linewidth=1, alpha=0.9, zorder=2)
    ax.axhline(avg_margin, linestyle="--", color="#9CA3AF", linewidth=1, alpha=0.9, zorder=2)

    # Quadrant corner labels (axes-fraction coordinates so they stay in corners)
    kw = dict(transform=ax.transAxes, fontsize=8, color="#D1D5DB", va="top")
    ax.text(0.02, 0.98, "Margin leaders",     ha="left",  **kw)
    ax.text(0.98, 0.98, "Revenue leaders",    ha="right", **kw)
    kw["va"] = "bottom"
    ax.text(0.02, 0.02, "Niche",              ha="left",  **kw)
    ax.text(0.98, 0.02, "Low-margin volume",  ha="right", **kw)

    # Category labels — offset direction based on quadrant to reduce overlap
    for _, row in df.iterrows():
        dx = 6 if row["net_revenue"] >= avg_rev else -6
        dy = 4 if row["estimated_net_margin_pct"] >= avg_margin else -4
        ax.annotate(
            row["category"],
            xy=(row["net_revenue"], row["estimated_net_margin_pct"]),
            xytext=(dx, dy),
            textcoords="offset points",
            fontsize=6.5,
            color="#374151",
            ha="left" if dx > 0 else "right",
        )

    # Format x-axis as $K / $M
    ax.xaxis.set_major_formatter(
        mticker.FuncFormatter(
            lambda v, _: f"${v / 1_000:.0f}K" if v < 1_000_000 else f"${v / 1_000_000:.1f}M"
        )
    )

    ax.set_xlabel("Net Revenue", fontsize=11)
    ax.set_ylabel("Estimated Net Margin (%)", fontsize=11)
    ax.set_title(
        "Product Revenue vs Margin Quadrant\n(bubble size = number of buyers)",
        fontsize=12, pad=12,
    )
    ax.legend(title="Strategic role", fontsize=8, title_fontsize=9, loc="lower right")
    ax.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    out = FIGURES_DIR / "revenue_margin_quadrant.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out.name}")


# ---------------------------------------------------------------------------
# Chart 4 — Bar chart: category count by strategic role
# ---------------------------------------------------------------------------

def chart_strategic_role_counts() -> None:
    df = pd.read_csv(TABLES_DIR / "product_category_recommendations.csv")

    counts = df["strategic_role"].value_counts()
    counts = counts.reindex([r for r in ROLE_ORDER if r in counts.index], fill_value=0)

    colors      = [ROLE_COLORS[r] for r in counts.index]
    short_labels = [ROLE_SHORT[r] for r in counts.index]

    fig, ax = plt.subplots(figsize=(10, 5))

    bars = ax.bar(
        range(len(counts)),
        counts.values,
        color=colors,
        width=0.6,
        zorder=3,
    )

    # Value label above each bar
    for bar, v in zip(bars, counts.values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.1,
            str(v),
            ha="center", va="bottom",
            fontsize=11, fontweight="bold", color="#374151",
        )

    ax.set_xticks(range(len(counts)))
    ax.set_xticklabels(short_labels, fontsize=9)
    ax.set_ylabel("Number of Categories", fontsize=11)
    ax.set_title("Category Count by Strategic Role", fontsize=12, pad=12)
    ax.set_ylim(0, counts.max() + 1.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.35, zorder=0)

    plt.tight_layout()
    out = FIGURES_DIR / "strategic_role_counts.png"
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out.name}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("\nE-Commerce Growth Analytics - Product Value Charts")
    print(f"Input:  {TABLES_DIR}")
    print(f"Output: {FIGURES_DIR}")
    print()

    print("Generating charts:")
    chart_first_vs_post()
    chart_lifetime_margin_vs_repeat()
    chart_revenue_margin_quadrant()
    chart_strategic_role_counts()

    print(f"\nDone. 4 charts written to {FIGURES_DIR.name}/")


if __name__ == "__main__":
    main()
