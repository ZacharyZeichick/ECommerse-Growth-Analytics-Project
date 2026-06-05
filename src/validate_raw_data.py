"""
validate_raw_data.py

Validates processed CSV files in data/processed/ using DuckDB.
Run from the repo root: python src/validate_raw_data.py
"""

from pathlib import Path
import duckdb

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_DIR = Path("data/processed")

EXPECTED_FILES = [
    "distribution_centers.csv",
    "events.csv",
    "inventory_items.csv",
    "orders.csv",
    "order_items.csv",
    "products.csv",
    "users.csv",
]

# Prior discovery row counts — WARN if actual differs by more than 5%
REFERENCE_COUNTS = {
    "users":                100_000,
    "orders":               125_408,
    "order_items":          181_815,
    "products":              29_120,
    "events":             2_429_781,
    "inventory_items":      489_994,
    "distribution_centers":      10,
}

WARN_THRESHOLD = 0.05  # 5%


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def run(con: duckdb.DuckDBPyConnection, sql: str) -> list:
    return con.execute(sql).fetchall()


def scalar(con: duckdb.DuckDBPyConnection, sql: str):
    return con.execute(sql).fetchone()[0]


def get_columns(filename: str) -> list[str]:
    """Read column names directly from the CSV header line in Python.

    Bypasses DuckDB's sniffer entirely — necessary because the processed files
    have \\r\\r\\n line endings that confuse DuckDB's dialect detection.
    """
    path = DATA_DIR / filename
    with open(path, encoding="utf-8") as f:
        header = f.readline()
    return [c.strip() for c in header.split(",")]


def csv_src(filename: str) -> str:
    """Return a DuckDB read_csv_auto expression for a processed (UTF-8) file."""
    p = str(DATA_DIR / filename).replace("\\", "/")
    return f"read_csv_auto('{p}')"


# ---------------------------------------------------------------------------
# Per-table validation
# ---------------------------------------------------------------------------

def validate_users(con: duckdb.DuckDBPyConnection, f: str) -> int:
    section("users")
    src = csv_src(f)
    rows     = scalar(con, f"SELECT COUNT(*) FROM {src}")
    null_id  = scalar(con, f"SELECT COUNT(*) FROM {src} WHERE id IS NULL")
    min_date = scalar(con, f"SELECT MIN(created_at) FROM {src}")
    max_date = scalar(con, f"SELECT MAX(created_at) FROM {src}")
    print(f"  rows:          {rows:,}")
    print(f"  null id:       {null_id:,}")
    print(f"  created_at:    {min_date}  ->  {max_date}")
    return rows


def validate_orders(con: duckdb.DuckDBPyConnection, f: str) -> int:
    section("orders")
    src = csv_src(f)
    rows        = scalar(con, f"SELECT COUNT(*) FROM {src}")
    null_id     = scalar(con, f"SELECT COUNT(*) FROM {src} WHERE order_id IS NULL")
    null_user   = scalar(con, f"SELECT COUNT(*) FROM {src} WHERE user_id IS NULL")
    min_date    = scalar(con, f"SELECT MIN(created_at) FROM {src}")
    max_date    = scalar(con, f"SELECT MAX(created_at) FROM {src}")
    status_dist = run(con, f"""
        SELECT status, COUNT(*) AS n
        FROM {src}
        GROUP BY status
        ORDER BY n DESC
    """)
    print(f"  rows:          {rows:,}")
    print(f"  null order_id: {null_id:,}")
    print(f"  null user_id:  {null_user:,}")
    print(f"  created_at:    {min_date}  ->  {max_date}")
    print("  status distribution:")
    for status, n in status_dist:
        print(f"    {status:<20} {n:>10,}")
    return rows


def validate_order_items(con: duckdb.DuckDBPyConnection, f: str) -> int:
    section("order_items")
    src = csv_src(f)
    rows         = scalar(con, f"SELECT COUNT(*) FROM {src}")
    null_id      = scalar(con, f"SELECT COUNT(*) FROM {src} WHERE id IS NULL")
    null_order   = scalar(con, f"SELECT COUNT(*) FROM {src} WHERE order_id IS NULL")
    null_user    = scalar(con, f"SELECT COUNT(*) FROM {src} WHERE user_id IS NULL")
    null_product = scalar(con, f"SELECT COUNT(*) FROM {src} WHERE product_id IS NULL")
    min_date     = scalar(con, f"SELECT MIN(created_at) FROM {src}")
    max_date     = scalar(con, f"SELECT MAX(created_at) FROM {src}")
    status_dist  = run(con, f"""
        SELECT status, COUNT(*) AS n
        FROM {src}
        GROUP BY status
        ORDER BY n DESC
    """)
    print(f"  rows:            {rows:,}")
    print(f"  null id:         {null_id:,}")
    print(f"  null order_id:   {null_order:,}")
    print(f"  null user_id:    {null_user:,}")
    print(f"  null product_id: {null_product:,}")
    print(f"  created_at:      {min_date}  ->  {max_date}")
    print("  status distribution:")
    for status, n in status_dist:
        print(f"    {status:<20} {n:>10,}")
    return rows


def validate_products(con: duckdb.DuckDBPyConnection, f: str) -> int:
    section("products")
    src = csv_src(f)
    rows        = scalar(con, f"SELECT COUNT(*) FROM {src}")
    null_id     = scalar(con, f"SELECT COUNT(*) FROM {src} WHERE id IS NULL")
    null_cost   = scalar(con, f"SELECT COUNT(*) FROM {src} WHERE cost IS NULL")
    null_retail = scalar(con, f"SELECT COUNT(*) FROM {src} WHERE retail_price IS NULL")
    print(f"  rows:              {rows:,}")
    print(f"  null id:           {null_id:,}")
    print(f"  null cost:         {null_cost:,}")
    print(f"  null retail_price: {null_retail:,}")
    return rows


def validate_inventory_items(con: duckdb.DuckDBPyConnection, f: str) -> int:
    section("inventory_items")
    src = csv_src(f)
    rows        = scalar(con, f"SELECT COUNT(*) FROM {src}")
    null_id     = scalar(con, f"SELECT COUNT(*) FROM {src} WHERE id IS NULL")
    null_prod   = scalar(con, f"SELECT COUNT(*) FROM {src} WHERE product_id IS NULL")
    null_cost   = scalar(con, f"SELECT COUNT(*) FROM {src} WHERE cost IS NULL")
    min_created = scalar(con, f"SELECT MIN(created_at) FROM {src}")
    max_created = scalar(con, f"SELECT MAX(created_at) FROM {src}")
    min_sold    = scalar(con, f"SELECT MIN(sold_at) FROM {src}")
    max_sold    = scalar(con, f"SELECT MAX(sold_at) FROM {src}")
    print(f"  rows:              {rows:,}")
    print(f"  null id:           {null_id:,}")
    print(f"  null product_id:   {null_prod:,}")
    print(f"  null cost:         {null_cost:,}")
    print(f"  created_at:        {min_created}  ->  {max_created}")
    print(f"  sold_at:           {min_sold}  ->  {max_sold}")
    return rows


def validate_events(con: duckdb.DuckDBPyConnection, f: str) -> int:
    section("events")
    src = csv_src(f)
    rows            = scalar(con, f"SELECT COUNT(*) FROM {src}")
    null_id         = scalar(con, f"SELECT COUNT(*) FROM {src} WHERE id IS NULL")
    null_session    = scalar(con, f"SELECT COUNT(*) FROM {src} WHERE session_id IS NULL")
    null_created    = scalar(con, f"SELECT COUNT(*) FROM {src} WHERE created_at IS NULL")
    null_traffic    = scalar(con, f"SELECT COUNT(*) FROM {src} WHERE traffic_source IS NULL")
    null_event_type = scalar(con, f"SELECT COUNT(*) FROM {src} WHERE event_type IS NULL")
    min_date        = scalar(con, f"SELECT MIN(created_at) FROM {src}")
    max_date        = scalar(con, f"SELECT MAX(created_at) FROM {src}")
    event_type_dist = run(con, f"""
        SELECT event_type, COUNT(*) AS n
        FROM {src}
        GROUP BY event_type
        ORDER BY n DESC
    """)
    print(f"  rows:                  {rows:,}")
    print(f"  null id:               {null_id:,}")
    print(f"  null session_id:       {null_session:,}")
    print(f"  null created_at:       {null_created:,}")
    print(f"  null traffic_source:   {null_traffic:,}")
    print(f"  null event_type:       {null_event_type:,}")
    print(f"  created_at:            {min_date}  ->  {max_date}")
    print("  event_type distribution:")
    for event_type, n in event_type_dist:
        print(f"    {str(event_type):<25} {n:>12,}")
    return rows


def validate_distribution_centers(con: duckdb.DuckDBPyConnection, f: str) -> int:
    section("distribution_centers")
    src = csv_src(f)
    rows    = scalar(con, f"SELECT COUNT(*) FROM {src}")
    null_id = scalar(con, f"SELECT COUNT(*) FROM {src} WHERE id IS NULL")
    print(f"  rows:    {rows:,}")
    print(f"  null id: {null_id:,}")
    return rows


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

VALIDATORS = {
    "users.csv":                validate_users,
    "orders.csv":               validate_orders,
    "order_items.csv":          validate_order_items,
    "products.csv":             validate_products,
    "inventory_items.csv":      validate_inventory_items,
    "events.csv":               validate_events,
    "distribution_centers.csv": validate_distribution_centers,
}


def main() -> None:
    print("\nE-Commerce Growth Analytics - Processed Data Validation")
    print(f"Data directory: {DATA_DIR.resolve()}")

    con = duckdb.connect()

    missing_files = []
    unreadable_files = []
    row_count_warnings = []

    # ------------------------------------------------------------------
    # File existence + size + column listing
    # ------------------------------------------------------------------
    section("FILE INVENTORY")
    for filename in EXPECTED_FILES:
        path = DATA_DIR / filename
        if not path.exists():
            print(f"  MISSING  {filename}")
            missing_files.append(filename)
            continue

        size_mb = path.stat().st_size / (1024 * 1024)
        try:
            cols = get_columns(filename)
            print(f"  {filename:<35} {size_mb:>7.2f} MB   cols: {len(cols)}")
            print(f"    columns: {', '.join(cols)}")
        except Exception as e:
            print(f"  ERROR reading {filename}: {e}")
            unreadable_files.append(filename)

    # ------------------------------------------------------------------
    # Per-table key validation checks
    # ------------------------------------------------------------------
    actual_counts: dict[str, int] = {}

    for filename in EXPECTED_FILES:
        path = DATA_DIR / filename
        if not path.exists() or filename in unreadable_files:
            continue
        validator = VALIDATORS.get(filename)
        if validator:
            try:
                actual_counts[filename] = validator(con, filename)
            except Exception as e:
                print(f"\n  ERROR during validation of {filename}: {e}")
                unreadable_files.append(filename)

    # ------------------------------------------------------------------
    # Row count comparison against reference counts
    # ------------------------------------------------------------------
    section("ROW COUNT COMPARISON")
    print(f"  {'Table':<25} {'Reference':>12} {'Actual':>12} {'Delta':>10}  Status")
    print(f"  {'-'*25} {'-'*12} {'-'*12} {'-'*10}  ------")

    for filename, ref_count in REFERENCE_COUNTS.items():
        csv_file = filename + ".csv"
        actual   = actual_counts.get(csv_file)

        if actual is None:
            print(f"  {filename:<25} {ref_count:>12,} {'N/A':>12}  {'-':>10}  SKIP")
            continue

        delta_pct = abs(actual - ref_count) / ref_count
        status = "OK"
        if delta_pct > WARN_THRESHOLD:
            status = "WARN"
            row_count_warnings.append(
                f"{filename}: expected ~{ref_count:,}, got {actual:,} ({delta_pct:.1%} diff)"
            )

        delta_str = f"{delta_pct:+.1%}" if actual != ref_count else "0.0%"
        print(f"  {filename:<25} {ref_count:>12,} {actual:>12,} {delta_str:>10}  {status}")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    section("SUMMARY")

    all_present  = len(missing_files) == 0
    all_readable = len(unreadable_files) == 0
    counts_ok    = len(row_count_warnings) == 0

    if all_present and all_readable:
        print("  FILE CHECK:   PASS - all expected files present and readable")
    else:
        if missing_files:
            print(f"  FILE CHECK:   FAIL - missing: {', '.join(missing_files)}")
        if unreadable_files:
            print(f"  READ CHECK:   FAIL - unreadable: {', '.join(unreadable_files)}")

    if counts_ok:
        print("  ROW COUNTS:   PASS - all within 5% of reference counts")
    else:
        print("  ROW COUNTS:   WARN - the following tables differ by >5%:")
        for w in row_count_warnings:
            print(f"    {w}")

    if not all_present or not all_readable:
        overall = "FAIL"
    elif not counts_ok:
        overall = "WARN"
    else:
        overall = "PASS"
    print(f"\n  OVERALL:      {overall}")

    con.close()


if __name__ == "__main__":
    main()
