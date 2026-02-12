"""
Ecuador Deep Dive — FRED
Two parts:
  1. Ecuador-specific series (FRED category 32696) — auto-discovered via API
  2. US monetary/financial series critical for dollarisation analysis
     (these are NOT available from IMF/World Bank)

NOTE on overlap: Many Ecuador series in FRED are sourced from the World Bank
or IMF (FRED is an aggregator). The auto-discovery approach grabs everything
so you have it in one place, but the metadata CSV flags the original source
so you can audit overlap.
"""

from fredapi import Fred
import pandas as pd
import requests
import time
import re
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
ECUADOR_CATEGORY_ID = 32696
OUTPUT_DIR = Path(__file__).parent / "ecuador_data" / "fred"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _label_to_filename(label: str) -> str:
    s = label.lower()
    s = s.replace("%", "pct").replace("&", "and").replace("/", "_")
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


# ═══════════════════════════════════════════════════════════════
# Part 2: US monetary/financial series (unique to FRED, not in IMF/WB)
# These matter because Ecuador uses the USD — US monetary policy
# IS Ecuador's monetary policy.
# ═══════════════════════════════════════════════════════════════
US_DOLLARISATION_SERIES = {
    # Fed policy
    "FEDFUNDS":         "US Fed Funds Rate",
    "DFEDTARU":         "US Fed Funds Upper Target",
    "DFEDTARL":         "US Fed Funds Lower Target",

    # US Treasury yields (Ecuador borrows in USD)
    "DGS2":             "US 2Y Treasury Yield",
    "DGS5":             "US 5Y Treasury Yield",
    "DGS10":            "US 10Y Treasury Yield",
    "DGS30":            "US 30Y Treasury Yield",
    "T10Y2Y":           "US 10Y-2Y Spread",

    # US inflation (directly impacts Ecuador's price level)
    "CPIAUCSL":         "US CPI (All Urban Consumers)",
    "CPILFESL":         "US Core CPI (ex Food & Energy)",
    "PCEPILFE":         "US Core PCE Price Index",

    # USD strength (affects Ecuador's trade competitiveness)
    "DTWEXBGS":         "USD Trade-Weighted Index (Broad Goods & Services)",
    "DTWEXEMEGS":       "USD Trade-Weighted Index (EME Goods & Services)",

    # US financial conditions
    "NFCI":             "Chicago Fed Financial Conditions Index",
    "STLFSI2":          "STL Fed Financial Stress Index",
    "BAMLH0A0HYM2":    "US High Yield OAS",
    "BAMLHE00EHYIOAS":  "US Emerging Markets Corporate OAS",
    "BAMLEMCLLCRPIOAS": "US LatAm Corporate OAS",

    # Oil prices (Ecuador is oil-dependent)
    "DCOILWTICO":       "WTI Crude Oil Price",
    "DCOILBRENTEU":     "Brent Crude Oil Price",

    # Commodity indices
    "PALLFNFINDEXM":    "All Commodity Price Index (IMF)",

    # EM risk / capital flows
    "TEDRATE":          "TED Spread",
    "VIXCLS":           "CBOE VIX",
}


def discover_ecuador_series(api_key: str) -> dict[str, str]:
    """Use FRED API to discover all series in the Ecuador category tree."""
    base_url = "https://api.stlouisfed.org/fred"
    all_series = {}

    def crawl_category(cat_id: int, depth: int = 0):
        # Get series in this category
        url = f"{base_url}/category/series"
        params = {
            "api_key": api_key,
            "category_id": cat_id,
            "file_type": "json",
            "limit": 1000,
        }
        try:
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
            for s in data.get("seriess", []):
                all_series[s["id"]] = s.get("title", s["id"])
        except Exception as e:
            print(f"  Warning: could not fetch series for category {cat_id}: {e}")

        time.sleep(0.3)

        # Recurse into child categories
        url = f"{base_url}/category/children"
        params = {
            "api_key": api_key,
            "category_id": cat_id,
            "file_type": "json",
        }
        try:
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            children = r.json().get("categories", [])
            for child in children:
                print(f"{'  ' * depth}  -> subcategory: {child['name']} ({child['id']})")
                crawl_category(child["id"], depth + 1)
        except Exception:
            pass

        time.sleep(0.2)

    print(f"Discovering all Ecuador series under FRED category {ECUADOR_CATEGORY_ID}...")
    crawl_category(ECUADOR_CATEGORY_ID)
    print(f"Found {len(all_series)} Ecuador-specific series.\n")
    return all_series


def download_series(fred: Fred, series_dict: dict[str, str], label_prefix: str) -> tuple[dict, list, list]:
    """Download a dict of {series_id: label}. Returns (data, metadata_rows, errors)."""
    data = {}
    metadata = []
    errors = []

    for i, (series_id, label) in enumerate(series_dict.items(), 1):
        print(f"  [{i}/{len(series_dict)}] {series_id:30s} — {label[:55]}...", end=" ", flush=True)
        try:
            series = fred.get_series(series_id)
            series.name = series_id

            # Drop NaNs for cleaner output
            series = series.dropna()
            if len(series) == 0:
                print("empty")
                continue

            data[series_id] = series

            # Save individual CSV
            df = series.to_frame(name="value")
            df.index.name = "date"
            fname = _label_to_filename(label)
            df.to_csv(OUTPUT_DIR / f"{fname}.csv")

            # Collect metadata
            try:
                info = fred.get_series_info(series_id)
                metadata.append({
                    "series_id": series_id,
                    "filename": fname + ".csv",
                    "label": label,
                    "title": info.get("title", ""),
                    "frequency": info.get("frequency_short", ""),
                    "units": info.get("units_short", ""),
                    "seasonal_adjustment": info.get("seasonal_adjustment_short", ""),
                    "last_updated": info.get("last_updated", ""),
                    "observation_start": info.get("observation_start", ""),
                    "observation_end": info.get("observation_end", ""),
                    "source": label_prefix,
                    "notes": info.get("notes", "")[:200],
                })
            except Exception:
                metadata.append({
                    "series_id": series_id,
                    "filename": fname + ".csv",
                    "label": label,
                    "source": label_prefix,
                })

            print(f"OK ({len(series)} obs)")
        except Exception as e:
            errors.append((series_id, label, str(e)))
            print(f"FAILED: {e}")

    return data, metadata, errors


def main():
    print("=" * 60)
    print("  Ecuador — FRED (Ecuador series + US dollarisation data)")
    print("=" * 60)

    fred = Fred(api_key=FRED_API_KEY)

    # -- Part 1: Auto-discover all Ecuador series --
    print("\n-- Part 1: Ecuador-specific series --\n")
    ecuador_series = discover_ecuador_series(FRED_API_KEY)
    ecu_data, ecu_meta, ecu_errors = download_series(fred, ecuador_series, "Ecuador (FRED)")

    # -- Part 2: US dollarisation-relevant series --
    print(f"\n-- Part 2: US dollarisation-relevant series ({len(US_DOLLARISATION_SERIES)} series) --\n")
    us_data, us_meta, us_errors = download_series(fred, US_DOLLARISATION_SERIES, "US Monetary/Financial (FRED)")

    # -- Combined metadata --
    all_meta = ecu_meta + us_meta
    all_errors = ecu_errors + us_errors

    meta_df = pd.DataFrame(all_meta)
    meta_path = OUTPUT_DIR / "_metadata.csv"
    meta_df.to_csv(meta_path, index=False)

    print(f"\n{'=' * 60}")
    print(f"  Summary")
    print(f"{'=' * 60}")
    print(f"  Ecuador series: {len(ecu_data)} downloaded, {len(ecu_errors)} failed")
    print(f"  US dollarisation series: {len(us_data)} downloaded, {len(us_errors)} failed")
    print(f"  Total series: {len(ecu_data) + len(us_data)}")
    print(f"  Metadata: {meta_path}")
    print(f"  Individual CSVs: {OUTPUT_DIR}")
    if all_errors:
        print(f"\n  {len(all_errors)} series failed:")
        for sid, label, err in all_errors:
            print(f"    {sid}: {label} — {err}")


if __name__ == "__main__":
    main()
