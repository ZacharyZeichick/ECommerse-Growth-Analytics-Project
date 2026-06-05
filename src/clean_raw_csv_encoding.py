"""
clean_raw_csv_encoding.py

Reads raw CSV files from data/raw/, decodes with UTF-8 (replacing any
invalid byte sequences), and writes clean UTF-8 copies to data/processed/.
Run from the repo root: python src/clean_raw_csv_encoding.py
"""

from pathlib import Path

DATA_RAW = Path("data/raw")
DATA_PROCESSED = Path("data/processed")


def clean_file(src: Path, dst: Path) -> None:
    raw_bytes = src.read_bytes()
    cleaned_text = raw_bytes.decode("utf-8", errors="replace")
    replacements = cleaned_text.count("�")
    dst.write_bytes(cleaned_text.encode("utf-8"))

    in_mb  = len(raw_bytes) / (1024 * 1024)
    out_mb = dst.stat().st_size / (1024 * 1024)

    status = f"  replacements: {replacements:,}" if replacements else "  replacements: 0 (file was clean)"
    print(f"  source:  {src}")
    print(f"  output:  {dst}")
    print(f"  size:    {in_mb:.2f} MB  ->  {out_mb:.2f} MB")
    print(status)


def main() -> None:
    print("\nE-Commerce Growth Analytics - CSV Encoding Cleaner")
    print(f"Source:      {DATA_RAW.resolve()}")
    print(f"Destination: {DATA_PROCESSED.resolve()}")

    csv_files = sorted(DATA_RAW.glob("*.csv"))
    if not csv_files:
        print("\nNo CSV files found in data/raw/. Nothing to do.")
        return

    print(f"\nFound {len(csv_files)} file(s) to process.\n")
    print("=" * 60)

    for src in csv_files:
        dst = DATA_PROCESSED / src.name
        print(f"\n{src.name}")
        clean_file(src, dst)

    print("\n" + "=" * 60)
    print(f"Done. {len(csv_files)} file(s) written to {DATA_PROCESSED}/")


if __name__ == "__main__":
    main()
