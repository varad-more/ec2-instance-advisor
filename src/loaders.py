from __future__ import annotations

import pandas as pd


def load_instances(path: str = "data/ec2_samples.csv") -> pd.DataFrame:
    """Load EC2 instance catalog with regional prices and performance features."""
    df = pd.read_csv(path)
    required = {
        "instance_type",
        "family",
        "instance_category",
        "region",
        "vcpus",
        "memory_gib",
        "network_score",
        "gpu_count",
        "price_usd_hour",
        "workload_tag",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    return df
