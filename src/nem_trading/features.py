from __future__ import annotations

import numpy as np
import pandas as pd

FEATURE_COLUMNS = ["RRP", "TOTALDEMAND", "price_change_30m", "hour"]


def build_features(frame: pd.DataFrame, spike_threshold: float = 150.0) -> pd.DataFrame:
    """Create simple time-series features and a next-30-minute spike target."""
    data = frame.sort_values("SETTLEMENTDATE").copy()
    data["hour"] = data["SETTLEMENTDATE"].dt.hour
    data["price_change_30m"] = data["RRP"] - data["RRP"].shift(6)

    future_prices = pd.concat([data["RRP"].shift(-step) for step in range(1, 7)], axis=1)
    data["future_max_30m"] = future_prices.max(axis=1)
    data["spike_next_30m"] = (data["future_max_30m"] >= spike_threshold).astype(float)
    data.loc[future_prices.isna().any(axis=1), "spike_next_30m"] = np.nan
    return data.dropna(subset=FEATURE_COLUMNS + ["spike_next_30m"]).reset_index(drop=True)
