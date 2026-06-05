"""
create_core_metric_charts.py
Creates five portfolio-ready charts from the core business metric CSVs.
Run from the repo root: python src/create_core_metric_charts.py
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
TABLES_DIR = REPO_ROOT / "outputs" / "tables"
FIGURES_DIR = REPO_ROOT / "outputs" / "figures"

FIGURES_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# 1. Monthly gross vs net revenue
# Excludes 2026-06 (partial month — only ~4 days of data)
# =============================================================================

df_monthly = pd.read_csv(TABLES_DIR / "monthly_business_metrics.csv")
df_monthly["order_month"] = pd.to_datetime(df_monthly["order_month"], format="%Y-%m")
df_monthly = df_monthly[df_monthly["order_month"].dt.strftime("%Y-%m") != "2026-06"]

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(df_monthly["order_month"], df_monthly["gross_revenue"], label="Gross Revenue", linewidth=1.5)
ax.plot(df_monthly["order_month"], df_monthly["net_revenue"], label="Net Revenue", linewidth=1.5)
ax.set_title("Monthly Gross vs. Net Revenue (2019–2026)", fontsize=14, pad=12)
ax.set_xlabel("Month")
ax.set_ylabel("Revenue ($)")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
ax.legend()
plt.tight_layout()
plt.savefig(FIGURES_DIR / "monthly_gross_vs_net_revenue.png", dpi=300, bbox_inches="tight")
plt.close()
print("Saved: monthly_gross_vs_net_revenue.png")


# =============================================================================
# 2. Top 10 categories by gross revenue
# =============================================================================

df_cat = pd.read_csv(TABLES_DIR / "category_business_metrics.csv")
top10_rev = df_cat.nlargest(10, "gross_revenue").sort_values("gross_revenue")

fig, ax = plt.subplots(figsize=(10, 6))
ax.barh(top10_rev["category"], top10_rev["gross_revenue"])
ax.set_title("Top 10 Categories by Gross Revenue", fontsize=14, pad=12)
ax.set_xlabel("Gross Revenue ($)")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
plt.tight_layout()
plt.savefig(FIGURES_DIR / "top_categories_by_gross_revenue.png", dpi=300, bbox_inches="tight")
plt.close()
print("Saved: top_categories_by_gross_revenue.png")


# =============================================================================
# 3. Top 10 categories by estimated net margin %
# Filtered to categories with gross_revenue >= $100K to exclude micro-categories
# =============================================================================

df_cat_filtered = df_cat[df_cat["gross_revenue"] >= 100_000]
top10_margin = df_cat_filtered.nlargest(10, "estimated_net_margin_pct").sort_values("estimated_net_margin_pct")

fig, ax = plt.subplots(figsize=(10, 6))
ax.barh(top10_margin["category"], top10_margin["estimated_net_margin_pct"])
ax.set_title(
    "Top 10 Categories by Estimated Net Margin %\n(Categories with $100K+ Gross Revenue)",
    fontsize=14, pad=12
)
ax.set_xlabel("Estimated Net Margin %")
ax.set_xlim(left=45)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.1f}%"))
plt.tight_layout()
plt.savefig(FIGURES_DIR / "top_categories_by_net_margin_pct.png", dpi=300, bbox_inches="tight")
plt.close()
print("Saved: top_categories_by_net_margin_pct.png")


# =============================================================================
# 4. Buyer segmentation: one-time vs repeat buyers
# =============================================================================

df_buyers = pd.read_csv(TABLES_DIR / "customer_purchase_summary.csv")
labels = ["One-Time Buyers", "Repeat Buyers"]
values = [int(df_buyers["one_time_buyers"].iloc[0]), int(df_buyers["repeat_buyers"].iloc[0])]

fig, ax = plt.subplots(figsize=(7, 5))
bars = ax.bar(labels, values)
ax.set_title("Buyer Segmentation: One-Time vs. Repeat Buyers", fontsize=14, pad=12)
ax.set_ylabel("Number of Buyers")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
for bar, value in zip(bars, values):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 400,
        f"{value:,}",
        ha="center", va="bottom", fontsize=11
    )
plt.tight_layout()
plt.savefig(FIGURES_DIR / "buyer_repeat_split.png", dpi=300, bbox_inches="tight")
plt.close()
print("Saved: buyer_repeat_split.png")


# =============================================================================
# 5. Order status distribution
# =============================================================================

df_status = pd.read_csv(TABLES_DIR / "order_status_rates.csv")

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(df_status["status"], df_status["orders"])
ax.set_title("Order Status Distribution", fontsize=14, pad=12)
ax.set_ylabel("Number of Orders")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
for bar, rate in zip(bars, df_status["status_rate"]):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 200,
        f"{rate:.1f}%",
        ha="center", va="bottom", fontsize=10
    )
plt.tight_layout()
plt.savefig(FIGURES_DIR / "order_status_distribution.png", dpi=300, bbox_inches="tight")
plt.close()
print("Saved: order_status_distribution.png")


print("\nAll charts saved to outputs/figures/")
