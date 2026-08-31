from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .features import FEATURE_COLUMNS


@dataclass
class SpikeModelResult:
    model: Pipeline
    train: pd.DataFrame
    test: pd.DataFrame
    metrics: dict[str, float]


def fit_spike_model(frame: pd.DataFrame, train_fraction: float = 0.7) -> SpikeModelResult:
    """Fit a chronologically split logistic regression for next-30-minute spikes."""
    if not 0.5 <= train_fraction < 1.0:
        raise ValueError("train_fraction must be between 0.5 and 1.0")

    split = int(len(frame) * train_fraction)
    train = frame.iloc[:split].copy()
    test = frame.iloc[split:].copy()

    model = Pipeline(
        [
            ("scale", StandardScaler()),
            ("logistic", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )
    model.fit(train[FEATURE_COLUMNS], train["spike_next_30m"])
    test["spike_probability"] = model.predict_proba(test[FEATURE_COLUMNS])[:, 1]
    predictions = (test["spike_probability"] >= 0.5).astype(int)

    metrics = {
        "accuracy": float(accuracy_score(test["spike_next_30m"], predictions)),
        "precision": float(precision_score(test["spike_next_30m"], predictions, zero_division=0)),
        "recall": float(recall_score(test["spike_next_30m"], predictions, zero_division=0)),
        "positive_rate": float(test["spike_next_30m"].mean()),
    }
    return SpikeModelResult(model=model, train=train, test=test, metrics=metrics)
