[Leer en español](README.es.md)

# Ecuador Macro Deep Dive

Data extraction pipeline for a comprehensive macroeconomic analysis of Ecuador, pulling from three major sources: the IMF, World Bank, and FRED.

Ecuador adopted the US dollar as legal tender in 2000, making it one of the largest dollarised economies in the world. This creates a unique analytical setup — US monetary policy effectively *is* Ecuador's monetary policy, so understanding the country requires layering macro fundamentals, development indicators, and US financial conditions together.

## Data Sources

| Script | Source | What it pulls |
|---|---|---|
| `ecuador_imf.py` | IMF DataMapper API | ~100+ macro indicators — GDP, government debt, fiscal balances, BOP, capital openness, inflation, WEO forecasts |
| `ecuador_worldbank.py` | World Bank v2 API (WDI) | ~1,500 development indicators — poverty, inequality, health, education, governance, environment, infrastructure |
| `ecuador_fred.py` | FRED API | ~300 Ecuador-specific series + 25 US monetary/financial series relevant to dollarisation |

### Why three sources?

- **IMF** covers the macro framework: what's happening to GDP, debt, the fiscal position, and the current account. It also provides 5-year forecasts via the World Economic Outlook.
- **World Bank** covers the structural/development layer: poverty, inequality, governance quality, access to services. Essential context for *why* the macro numbers look the way they do.
- **FRED** is an aggregator — much of its international data originates from the IMF and World Bank. But it uniquely provides US monetary policy data (Fed funds rate, Treasury yields, financial conditions indices), oil prices, and EM risk spreads. For a dollarised economy, this is indispensable.

## Setup

### Requirements

```
pip install requests fredapi pandas python-dotenv
```

### FRED API Key

Get a free key from [FRED](https://fred.stlouisfed.org/docs/api/api_key.html) and create a `.env` file in the project root:

```
FRED_API_KEY=your_key_here
```

The IMF and World Bank APIs do not require authentication.

## Usage

Run all three extractors sequentially with the orchestrator script:

```bash
python ecuador_run_all.py
```

Or run them individually:

```bash
python ecuador_imf.py         # ~5 min
python ecuador_worldbank.py   # ~20-30 min (iterates ~1,500 indicators)
python ecuador_fred.py        # ~5-10 min
```

## Output

```
ecuador_data/
├── imf/
│   ├── ecuador_imf_all_indicators.csv   # Wide format: Year x indicators
│   └── indicator_metadata.csv           # Indicator catalogue with year coverage
├── worldbank/
│   ├── ecuador_wb_all_indicators.csv    # Wide format: Year x indicators
│   └── indicator_metadata.csv           # Indicator catalogue with topics and sources
└── fred/
    ├── _metadata.csv                    # Full metadata (flags original source for overlap audit)
    ├── us_fed_funds_rate.csv            # Individual series files
    ├── wti_crude_oil_price.csv
    └── ...
```

The FRED metadata CSV includes a `source` column and `notes` field so you can identify which series are World Bank/IMF pass-throughs versus genuinely unique FRED data.
