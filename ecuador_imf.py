"""
Ecuador Deep Dive — IMF DataMapper
Fetches all available IMF DataMapper indicators for Ecuador.
Outputs a single wide CSV plus indicator metadata.
"""

import requests
import time
import csv
from pathlib import Path

BASE = "https://www.imf.org/external/datamapper/api/v1"
COUNTRY = "ECU"
OUTPUT_DIR = Path(__file__).parent / "ecuador_data" / "imf"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_json(url: str, retries: int = 3) -> dict | None:
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"  FAILED: {e}")
                return None


def fetch_indicators() -> dict[str, str]:
    """Return {indicator_code: label} for all available indicators."""
    data = get_json(f"{BASE}/indicators")
    if not data:
        return {}
    raw = data.get("indicators", {})
    return {code: (meta.get("label") or code) for code, meta in raw.items()}


def fetch_indicator_data(code: str) -> dict[str, float]:
    """Fetch one indicator for ECU. Returns {year: value}."""
    data = get_json(f"{BASE}/{code}/{COUNTRY}")
    if not data or "values" not in data:
        return {}
    series = data["values"].get(code, {})
    return series.get(COUNTRY, {})


def build_panel(all_data: dict, indicators: dict) -> list[dict]:
    """Reshape into rows: Year, indicator1, indicator2, ..."""
    all_years = set()
    for code, year_dict in all_data.items():
        all_years.update(year_dict.keys())

    rows = []
    for year in sorted(all_years):
        row = {"Year": year}
        for code, label in sorted(indicators.items(), key=lambda x: x[1]):
            value = all_data.get(code, {}).get(year)
            row[f"{label} [{code}]"] = value if value is not None else ""
        rows.append(row)
    return rows


def main():
    print("=" * 60)
    print("  Ecuador — IMF DataMapper (all indicators)")
    print("=" * 60)

    print("\nFetching indicator list...")
    indicators = fetch_indicators()
    print(f"Found {len(indicators)} indicators.\n")

    all_data: dict[str, dict[str, float]] = {}
    success = 0
    empty = 0
    failed = 0

    for i, (code, label) in enumerate(sorted(indicators.items(), key=lambda x: x[1]), 1):
        print(f"[{i}/{len(indicators)}] {code}: {label}...", end=" ", flush=True)
        result = fetch_indicator_data(code)
        if result and len(result) > 0:
            all_data[code] = result
            success += 1
            print(f"OK ({len(result)} years)")
        elif result is not None:
            empty += 1
            print("no data for ECU")
        else:
            failed += 1
            print("skipped")

        # Rate limit: ~10 requests per 5 seconds
        if i % 8 == 0:
            time.sleep(1.5)

    print(f"\nResults: {success} with data, {empty} empty, {failed} failed\n")

    # Build and write CSV
    kept = {k: v for k, v in indicators.items() if k in all_data}
    rows = build_panel(all_data, kept)

    out_path = OUTPUT_DIR / "ecuador_imf_all_indicators.csv"
    if rows:
        fieldnames = rows[0].keys()
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Wrote {len(rows)} rows x {len(kept)} indicators to:\n  {out_path}")
    else:
        print("No data retrieved.")

    # Metadata
    meta_path = OUTPUT_DIR / "indicator_metadata.csv"
    with open(meta_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["code", "label", "years_available"])
        writer.writeheader()
        for code, label in sorted(kept.items(), key=lambda x: x[1]):
            years = sorted(all_data[code].keys())
            span = f"{years[0]}-{years[-1]}" if years else ""
            writer.writerow({"code": code, "label": label, "years_available": span})
    print(f"Wrote indicator metadata to:\n  {meta_path}")


if __name__ == "__main__":
    main()
