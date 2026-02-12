[Read in English](README.md)

# Ecuador — Análisis Macro a Fondo

Pipeline de extracción de datos para un análisis macroeconómico integral de Ecuador, utilizando tres fuentes principales: el FMI, el Banco Mundial y FRED.

Ecuador adoptó el dólar estadounidense como moneda de curso legal en el año 2000, convirtiéndose en una de las economías dolarizadas más grandes del mundo. Esto genera un escenario analítico único: la política monetaria de EE.UU. es, en la práctica, la política monetaria de Ecuador. Por ello, comprender al país requiere combinar fundamentos macroeconómicos, indicadores de desarrollo y condiciones financieras estadounidenses.

## Fuentes de Datos

| Script | Fuente | Qué extrae |
|---|---|---|
| `ecuador_imf.py` | API DataMapper del FMI | ~100+ indicadores macro — PIB, deuda pública, balances fiscales, balanza de pagos, apertura de capital, inflación, proyecciones del WEO |
| `ecuador_worldbank.py` | API v2 del Banco Mundial (IDM) | ~1.500 indicadores de desarrollo — pobreza, desigualdad, salud, educación, gobernanza, medio ambiente, infraestructura |
| `ecuador_fred.py` | API de FRED | ~300 series específicas de Ecuador + 25 series monetarias/financieras de EE.UU. relevantes para la dolarización |

### ¿Por qué tres fuentes?

- **FMI** cubre el marco macro: qué sucede con el PIB, la deuda, la posición fiscal y la cuenta corriente. También ofrece proyecciones a 5 años a través del World Economic Outlook.
- **Banco Mundial** cubre la capa estructural/de desarrollo: pobreza, desigualdad, calidad de gobernanza, acceso a servicios. Contexto esencial para entender *por qué* los números macro son como son.
- **FRED** es un agregador — gran parte de sus datos internacionales provienen del FMI y el Banco Mundial. Pero ofrece de forma única datos de política monetaria de EE.UU. (tasa de fondos federales, rendimientos del Tesoro, índices de condiciones financieras), precios del petróleo y spreads de riesgo de mercados emergentes. Para una economía dolarizada, esto es indispensable.

## Configuración

### Requisitos

```
pip install requests fredapi pandas python-dotenv
```

### Clave API de FRED

Obtén una clave gratuita en [FRED](https://fred.stlouisfed.org/docs/api/api_key.html) y crea un archivo `.env` en la raíz del proyecto:

```
FRED_API_KEY=tu_clave_aqui
```

Las APIs del FMI y del Banco Mundial no requieren autenticación.

## Uso

Ejecuta los tres extractores de forma secuencial con el script orquestador:

```bash
python ecuador_run_all.py
```

O ejecútalos individualmente:

```bash
python ecuador_imf.py         # ~5 min
python ecuador_worldbank.py   # ~20-30 min (itera ~1.500 indicadores)
python ecuador_fred.py        # ~5-10 min
```

## Salida

```
ecuador_data/
├── imf/
│   ├── ecuador_imf_all_indicators.csv   # Formato ancho: Año x indicadores
│   └── indicator_metadata.csv           # Catálogo de indicadores con cobertura temporal
├── worldbank/
│   ├── ecuador_wb_all_indicators.csv    # Formato ancho: Año x indicadores
│   └── indicator_metadata.csv           # Catálogo de indicadores con temas y fuentes
└── fred/
    ├── _metadata.csv                    # Metadatos completos (identifica la fuente original)
    ├── us_fed_funds_rate.csv            # Archivos de series individuales
    ├── wti_crude_oil_price.csv
    └── ...
```

El CSV de metadatos de FRED incluye una columna `source` y un campo `notes` para identificar qué series son réplicas del Banco Mundial/FMI y cuáles son datos genuinamente únicos de FRED.
