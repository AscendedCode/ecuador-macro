"""
Ecuador Deep Dive — World Bank (World Development Indicators)
Fetches all WDI indicators for Ecuador via the v2 API.
Outputs a single wide CSV plus indicator metadata.
"""

import requests
import time
import csv
from pathlib import Path

API_BASE = "https://api.worldbank.org/v2"
COUNTRY = "ECU"
SOURCE = 2  # World Development Indicators
OUTPUT_DIR = Path(__file__).parent / "ecuador_data" / "worldbank"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_json(url: str, params: dict | None = None, retries: int = 3) -> list | None:
    base_params = {"format": "json", "per_page": 10000}
    if params:
        base_params.update(params)
    for attempt in range(retries):
        try:
            r = requests.get(url, params=base_params, timeout=60)
            r.raise_for_status()
            data = r.json()
            # WB API returns [metadata, records] — we want the records
            if isinstance(data, list) and len(data) == 2:
                return data
            return None
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"  FAILED: {e}")
                return None


def fetch_all_indicators() -> list[dict]:
    """Get the full list of WDI indicator codes and names."""
    indicators = []
    page = 1
    while True:
        resp = get_json(f"{API_BASE}/indicator", params={"source": SOURCE, "page": page, "per_page": 1000})
        if not resp or not resp[1]:
            break
        meta, records = resp
        indicators.extend(records)
        if page >= meta.get("pages", 1):
            break
        page += 1
        time.sleep(0.3)
    return indicators


def fetch_indicator_data(indicator_id: str) -> dict[str, float | None]:
    """Fetch all years of one indicator for Ecuador. Returns {year: value}."""
    resp = get_json(f"{API_BASE}/country/{COUNTRY}/indicator/{indicator_id}")
    if not resp or not resp[1]:
        return {}
    result = {}
    for record in resp[1]:
        year = record.get("date")
        value = record.get("value")
        if year and value is not None:
            result[year] = value
    return result


def main():
    print("=" * 60)
    print("  Ecuador — World Bank (World Development Indicators)")
    print("=" * 60)

    print("\nFetching indicator list (source=WDI)...")
    all_indicators = fetch_all_indicators()
    print(f"Found {len(all_indicators)} indicators.\n")

    all_data: dict[str, dict[str, float]] = {}
    indicator_info: dict[str, dict] = {}
    success = 0
    empty = 0
    failed = 0

    for i, ind in enumerate(all_indicators, 1):
        code = ind["id"]
        name = ind.get("name", code)
        source_org = ind.get("sourceOrganization", "")
        topics = ", ".join(t.get("value", "") for t in ind.get("topics", []) if t.get("value"))

        print(f"[{i}/{len(all_indicators)}] {code}: {name[:60]}...", end=" ", flush=True)

        result = fetch_indicator_data(code)
        if result:
            all_data[code] = result
            indicator_info[code] = {
                "code": code,
                "name": name,
                "source_org": source_org,
                "topics": topics,
            }
            success += 1
            print(f"OK ({len(result)} years)")
        else:
            empty += 1
            print("no data")

        # Rate limit: be gentle with the WB API
        if i % 15 == 0:
            time.sleep(1.0)
        else:
            time.sleep(0.15)

    print(f"\nResults: {success} with data, {empty} empty, {failed} failed\n")

    # Collect all years
    all_years = set()
    for year_dict in all_data.values():
        all_years.update(year_dict.keys())

    # Build wide CSV
    rows = []
    for year in sorted(all_years):
        row = {"Year": year}
        for code in sorted(all_data.keys()):
            value = all_data[code].get(year)
            row[f"{indicator_info[code]['name']} [{code}]"] = value if value is not None else ""
        rows.append(row)

    out_path = OUTPUT_DIR / "ecuador_wb_all_indicators.csv"
    if rows:
        fieldnames = list(rows[0].keys())
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Wrote {len(rows)} rows x {len(all_data)} indicators to:\n  {out_path}")
    else:
        print("No data retrieved.")

    # Metadata
    meta_path = OUTPUT_DIR / "indicator_metadata.csv"
    with open(meta_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["code", "name", "source_org", "topics", "years_available"])
        writer.writeheader()
        for code in sorted(indicator_info.keys()):
            info = indicator_info[code]
            years = sorted(all_data[code].keys())
            span = f"{years[0]}-{years[-1]}" if years else ""
            writer.writerow({**info, "years_available": span})
    print(f"Wrote indicator metadata ({len(indicator_info)} indicators) to:\n  {meta_path}")


if __name__ == "__main__":
    main()
