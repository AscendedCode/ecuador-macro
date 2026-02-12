"""
Ecuador Deep Dive — Run All Extractors
Runs all three data sources sequentially and prints a final audit summary.
"""

import subprocess
import sys
import time
from pathlib import Path

SCRIPTS = [
    ("IMF DataMapper",   "ecuador_imf.py"),
    ("World Bank (WDI)", "ecuador_worldbank.py"),
    ("FRED",             "ecuador_fred.py"),
]

ROOT = Path(__file__).parent


def count_csvs(directory: Path) -> tuple[int, int]:
    """Return (num_csv_files, total_rows across all csvs)."""
    if not directory.exists():
        return 0, 0
    csv_files = list(directory.glob("*.csv"))
    total_rows = 0
    for f in csv_files:
        try:
            total_rows += sum(1 for _ in open(f, encoding="utf-8")) - 1  # minus header
        except Exception:
            pass
    return len(csv_files), total_rows


def main():
    print("=" * 70)
    print("  ECUADOR DEEP DIVE — DATA EXTRACTION PIPELINE")
    print("=" * 70)

    results = {}

    for name, script in SCRIPTS:
        print(f"\n{'─' * 70}")
        print(f"  Running: {name} ({script})")
        print(f"{'─' * 70}\n")

        start = time.time()
        try:
            result = subprocess.run(
                [sys.executable, str(ROOT / script)],
                cwd=str(ROOT),
                timeout=1800,  # 30 min max per script
            )
            elapsed = time.time() - start
            results[name] = {"status": "OK" if result.returncode == 0 else "ERROR", "time": elapsed}
        except subprocess.TimeoutExpired:
            results[name] = {"status": "TIMEOUT", "time": 1800}
        except Exception as e:
            results[name] = {"status": f"FAILED: {e}", "time": 0}

    # ── Final audit ──
    print(f"\n\n{'=' * 70}")
    print("  FINAL AUDIT SUMMARY")
    print(f"{'=' * 70}\n")

    data_dirs = {
        "IMF DataMapper":   ROOT / "ecuador_data" / "imf",
        "World Bank (WDI)": ROOT / "ecuador_data" / "worldbank",
        "FRED":             ROOT / "ecuador_data" / "fred",
    }

    for name, script in SCRIPTS:
        status = results.get(name, {})
        ddir = data_dirs.get(name)
        n_files, n_rows = count_csvs(ddir) if ddir else (0, 0)
        elapsed = status.get("time", 0)

        print(f"  {name:25s}  {status.get('status', '?'):10s}  "
              f"{n_files:4d} files  {n_rows:7,d} rows  ({elapsed:.0f}s)")

    total_files = sum(count_csvs(d)[0] for d in data_dirs.values() if d.exists())
    total_rows = sum(count_csvs(d)[1] for d in data_dirs.values() if d.exists())
    print(f"\n  {'TOTAL':25s}  {'':10s}  {total_files:4d} files  {total_rows:7,d} rows")
    print(f"\n  Output directory: {ROOT / 'ecuador_data'}")
    print()


if __name__ == "__main__":
    main()
