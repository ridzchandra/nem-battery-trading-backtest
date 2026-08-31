from __future__ import annotations

import pandas as pd


def threshold_signal(row: pd.Series) -> str:
    if row["RRP"] <= 30:
        return "charge"
    if row["RRP"] >= 150:
        return "discharge"
    return "idle"


def time_aware_signal(row: pd.Series) -> str:
    hour = row["SETTLEMENTDATE"].hour
    if row["RRP"] <= 35:
        return "charge"
    if 16 <= hour <= 21 and row["RRP"] >= 120:
        return "discharge"
    if row["RRP"] >= 300:
        return "discharge"
    return "idle"


def probability_aware_signal(row: pd.Series) -> str:
    if row["RRP"] <= 30:
        return "charge"
    if row["RRP"] >= 300:
        return "discharge"
    if row["RRP"] >= 150 and row.get("spike_probability", 0.0) < 0.5:
        return "discharge"
    return "idle"
