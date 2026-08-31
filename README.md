# NEM Battery Trading Backtest

A small electricity-market project using public Australian Energy Market Operator (AEMO) data to explore NSW spot-price behaviour and test simple battery trading rules.

The project deliberately uses transparent assumptions and simple models. The main focus is the trading logic: how 5-minute electricity prices, battery constraints, transaction timing and price-spike probabilities translate into P&L.

## What it does

- Downloads public `PUBLIC_PRICES` files from AEMO NEMWeb.
- Extracts NSW (`NSW1`) 5-minute regional prices and demand.
- Models a 100 MWh / 50 MW battery with 95% charge and discharge efficiency.
- Backtests two rules-based strategies:
  - **Threshold:** charge at or below $30/MWh and discharge at or above $150/MWh.
  - **Time-aware:** use a lower evening discharge threshold while keeping a high out-of-peak threshold.
- Fits a simple logistic regression estimating whether price will exceed $150/MWh in the next 30 minutes.
- Uses that probability in a third battery strategy that can preserve stored energy when another near-term spike looks likely.
- Produces strategy P&L summaries and charts.

## Project structure

```text
.
├── data/
│   ├── raw/                 # downloaded AEMO zip files (gitignored)
│   └── processed/           # parsed NSW price data (gitignored)
├── notebooks/
│   └── 01_nem_battery_backtest.ipynb
├── outputs/                 # generated charts and summary CSVs
├── scripts/
│   ├── download_data.py
│   └── run_analysis.py
├── src/nem_trading/
│   ├── aemo.py
│   ├── backtest.py
│   ├── battery.py
│   ├── features.py
│   ├── model.py
│   └── strategies.py
└── tests/
```

## Setup

Python 3.11+ is recommended.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

## Download AEMO data

For completed archive months:

```bash
python scripts/download_data.py --months 2026-05 2026-06
```

For recent daily files currently listed by NEMWeb:

```bash
python scripts/download_data.py --recent-days 30
```

Both commands create:

```text
data/processed/nsw1_prices.csv
```

Monthly archive publication can lag the current month. Use `--recent-days` for recent periods that are not yet available as a monthly archive.

## Run the analysis

```bash
python scripts/run_analysis.py
```

Generated files are written to `outputs/`:

```text
outputs/price_series.png
outputs/strategy_pnl.png
outputs/strategy_summary.csv
```

The terminal also prints the logistic-regression test metrics and the P&L summary for each strategy.

## Run the notebook

```bash
jupyter notebook notebooks/01_nem_battery_backtest.ipynb
```

The notebook follows the same workflow interactively: inspect prices, create model features, fit the spike model, run the strategies and compare results.

## Run tests

```bash
pytest
```

## Main assumptions

- Dispatch intervals are 5 minutes.
- Battery energy capacity is 100 MWh.
- Maximum charge/discharge power is 50 MW.
- Charge efficiency is 95% and discharge efficiency is 95%.
- No degradation cost, FCAS revenue, bidding constraints or market-impact costs are included.
- The backtest is a simplified spot-arbitrage exercise, not a production battery dispatch model.
- Model training and testing are split chronologically rather than randomly to avoid using future observations to predict the past.

## Data source

Market data is downloaded from AEMO NEMWeb `PUBLIC_PRICES` reports:

- `https://www.nemweb.com.au/Reports/CURRENT/Public_Prices/`
- `https://www.nemweb.com.au/Reports/ARCHIVE/Public_Prices/`
