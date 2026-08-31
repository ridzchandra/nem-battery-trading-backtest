from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from nem_trading.backtest import run_backtest, summarise_backtest
from nem_trading.features import build_features
from nem_trading.model import fit_spike_model
from nem_trading.strategies import probability_aware_signal, threshold_signal, time_aware_signal


def save_price_chart(frame: pd.DataFrame, output_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(frame["SETTLEMENTDATE"], frame["RRP"], linewidth=0.7)
    ax.set_title("NSW NEM spot price")
    ax.set_ylabel("RRP ($/MWh)")
    ax.set_xlabel("Time")
    fig.tight_layout()
    fig.savefig(output_dir / "price_series.png", dpi=160)
    plt.close(fig)


def save_pnl_chart(results: dict[str, pd.DataFrame], output_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 5))
    for name, result in results.items():
        ax.plot(result["SETTLEMENTDATE"], result["cumulative_pnl"], label=name)
    ax.set_title("Battery strategy cumulative P&L")
    ax.set_ylabel("P&L ($)")
    ax.set_xlabel("Time")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "strategy_pnl.png", dpi=160)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the NEM battery trading analysis.")
    parser.add_argument("--input", default="data/processed/nsw1_prices.csv")
    args = parser.parse_args()

    frame = pd.read_csv(args.input, parse_dates=["SETTLEMENTDATE"]).sort_values("SETTLEMENTDATE")
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    features = build_features(frame)
    model_result = fit_spike_model(features)

    threshold = run_backtest(model_result.test, threshold_signal)
    time_aware = run_backtest(model_result.test, time_aware_signal)
    probability = run_backtest(model_result.test, probability_aware_signal)

    results = {
        "Threshold": threshold,
        "Time-aware": time_aware,
        "Probability-aware": probability,
    }

    summary_rows = []
    for name, result in results.items():
        summary_rows.append({"strategy": name, **summarise_backtest(result)})
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(output_dir / "strategy_summary.csv", index=False)

    save_price_chart(model_result.test, output_dir)
    save_pnl_chart(results, output_dir)

    print("Logistic regression test metrics:")
    for name, value in model_result.metrics.items():
        print(f"  {name}: {value:.3f}")
    print("\nStrategy summary:")
    print(summary.to_string(index=False))
    print("\nCharts and CSV summary written to outputs/")


if __name__ == "__main__":
    main()
