from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.advisor import Weights, score_instances
from src.loaders import load_instances

CATEGORY_EXPLAIN = {
    "CPU": "Best for compute-heavy tasks like builds, APIs under load, and transcoding.",
    "GPU": "Best for ML training/inference, graphics rendering, and CUDA workloads.",
    "Memory": "Best for large in-memory datasets, caching layers, and JVM-heavy services.",
    "Storage": "Best for high IOPS / low-latency local NVMe workloads.",
    "General": "Balanced default for most web apps and microservices.",
}

st.set_page_config(page_title="EC2 Instance Advisor", layout="wide")
st.title("EC2 Instance Advisor")
st.caption("Pick the best EC2 instance by balancing regional price and performance.")

df = load_instances()

with st.sidebar:
    st.header("Filters")
    regions = sorted(df["region"].unique().tolist())
    categories = sorted(df["instance_category"].unique().tolist())

    selected_regions = st.multiselect("Regions", regions, default=regions)
    selected_categories = st.multiselect("Instance categories", categories, default=categories)

    st.header("Scoring Weights")
    w_price = st.slider("Price importance", 0.0, 1.0, 0.35, 0.05)
    w_cpu = st.slider("CPU importance", 0.0, 1.0, 0.25, 0.05)
    w_mem = st.slider("Memory importance", 0.0, 1.0, 0.2, 0.05)
    w_net = st.slider("Network importance", 0.0, 1.0, 0.1, 0.05)
    w_gpu = st.slider("GPU importance", 0.0, 1.0, 0.1, 0.05)

subset = df[
    df["region"].isin(selected_regions) & df["instance_category"].isin(selected_categories)
].copy()

if subset.empty:
    st.warning("No instances match your filters.")
    st.stop()

w_sum = w_price + w_cpu + w_mem + w_net + w_gpu
if w_sum == 0:
    st.error("At least one weight must be > 0.")
    st.stop()

weights = Weights(
    price=w_price / w_sum,
    cpu=w_cpu / w_sum,
    memory=w_mem / w_sum,
    network=w_net / w_sum,
)

ranked = score_instances(subset, weights)
ranked["gpu_norm"] = ranked["gpu_count"] / max(ranked["gpu_count"].max(), 1)
ranked["composite_score"] = ranked["composite_score"] * (1 - (w_gpu / w_sum)) + ranked["gpu_norm"] * (w_gpu / w_sum)
ranked = ranked.sort_values("composite_score", ascending=False)

best = ranked.iloc[0]
st.success(
    f"Top recommendation: **{best['instance_type']}** ({best['instance_category']}, {best['region']}) at "
    f"**${best['price_usd_hour']:.3f}/hr** (score {best['composite_score']:.3f})"
)
st.info(CATEGORY_EXPLAIN.get(best["instance_category"], ""))

with st.expander("Instance type explanations"):
    for k, v in CATEGORY_EXPLAIN.items():
        st.write(f"- **{k}**: {v}")

col1, col2 = st.columns([1.1, 1])

with col1:
    st.subheader("Top Candidates")
    st.dataframe(
        ranked[[
            "instance_type", "instance_category", "family", "region", "vcpus", "memory_gib",
            "gpu_count", "network_score", "price_usd_hour", "composite_score",
        ]].head(20),
        use_container_width=True,
        hide_index=True,
    )

with col2:
    st.subheader("Price vs Performance")
    ranked["perf_index"] = (
        ranked["vcpus"] * 0.35 + ranked["memory_gib"] * 0.30 + ranked["network_score"] * 0.2 + ranked["gpu_count"] * 0.15
    )
    fig = px.scatter(
        ranked,
        x="price_usd_hour",
        y="perf_index",
        color="instance_category",
        size="composite_score",
        hover_name="instance_type",
        hover_data=["region", "vcpus", "memory_gib", "gpu_count", "network_score"],
        title="Lower-left is cheaper, upper-right is stronger",
    )
    st.plotly_chart(fig, use_container_width=True)
