from __future__ import annotations

from dataclasses import dataclass
import pandas as pd


@dataclass
class Weights:
    price: float = 0.4
    cpu: float = 0.3
    memory: float = 0.2
    network: float = 0.1


def _normalize(series: pd.Series, reverse: bool = False) -> pd.Series:
    min_v, max_v = series.min(), series.max()
    if max_v == min_v:
        return pd.Series([1.0] * len(series), index=series.index)
    norm = (series - min_v) / (max_v - min_v)
    return 1.0 - norm if reverse else norm


def score_instances(df: pd.DataFrame, weights: Weights) -> pd.DataFrame:
    out = df.copy()

    out["score_price"] = _normalize(out["price_usd_hour"], reverse=True)
    out["score_cpu"] = _normalize(out["vcpus"])
    out["score_memory"] = _normalize(out["memory_gib"])
    out["score_network"] = _normalize(out["network_score"])

    out["composite_score"] = (
        weights.price * out["score_price"]
        + weights.cpu * out["score_cpu"]
        + weights.memory * out["score_memory"]
        + weights.network * out["score_network"]
    )

    return out.sort_values("composite_score", ascending=False)
