import pandas as pd

from nem_trading.features import build_features


def test_spike_target_only_uses_future_rows():
    times = pd.date_range("2026-01-01", periods=20, freq="5min")
    prices = [50.0] * 20
    prices[10] = 200.0
    frame = pd.DataFrame(
        {
            "SETTLEMENTDATE": times,
            "REGIONID": "NSW1",
            "RRP": prices,
            "TOTALDEMAND": 8000.0,
        }
    )
    features = build_features(frame, spike_threshold=150)
    row = features.loc[features["SETTLEMENTDATE"] == times[4]].iloc[0]
    assert row["spike_next_30m"] == 1
