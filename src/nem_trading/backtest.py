from __future__ import annotations

from collections.abc import Callable

import pandas as pd

from .battery import Battery

SignalFunction = Callable[[pd.Series], str]


def run_backtest(
    frame: pd.DataFrame,
    signal_function: SignalFunction,
    battery: Battery | None = None,
    interval_minutes: int = 5,
) -> pd.DataFrame:
    """Run a sequential battery backtest using only information in each row."""
    battery = battery or Battery()
    rows = []
    cumulative_pnl = 0.0

    for _, row in frame.sort_values("SETTLEMENTDATE").iterrows():
        action = signal_function(row)
        energy_mwh = 0.0
        cashflow = 0.0

        if action == "charge":
            energy_mwh, cashflow = battery.charge(row["RRP"], interval_minutes)
            energy_mwh = -energy_mwh
        elif action == "discharge":
            energy_mwh, cashflow = battery.discharge(row["RRP"], interval_minutes)

        cumulative_pnl += cashflow
        rows.append(
            {
                "SETTLEMENTDATE": row["SETTLEMENTDATE"],
                "RRP": row["RRP"],
                "action": action,
                "energy_mwh": energy_mwh,
                "cashflow": cashflow,
                "cumulative_pnl": cumulative_pnl,
                "state_of_charge_mwh": battery.state_of_charge_mwh,
            }
        )

    return pd.DataFrame(rows)


def summarise_backtest(result: pd.DataFrame) -> dict[str, float]:
    daily = result.set_index("SETTLEMENTDATE")["cashflow"].resample("D").sum()
    return {
        "total_pnl": float(result["cashflow"].sum()),
        "traded_mwh": float(result["energy_mwh"].abs().sum()),
        "active_intervals": float((result["action"] != "idle").sum()),
        "best_day": float(daily.max()) if not daily.empty else 0.0,
        "worst_day": float(daily.min()) if not daily.empty else 0.0,
    }
