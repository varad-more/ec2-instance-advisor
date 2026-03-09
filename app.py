from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.advisor import Weights, score_instances
from src.loaders import load_instances


st.set_page_config(page_title="EC2 Instance Advisor", layout="wide")
st.title("EC2 Instance Advisor")
st.caption("Pick the best EC2 instance by balancing regional price and performance.")


df = load_instances()

with st.sidebar:
    st.header("Filters")
    regions = sorted(df["region"].unique().tolist())
    workloads = sorted(df["workload_tag"].unique().tolist())

    selected_regions = st.multiselect("Regions", regions, default=regions)
    selected_workloads = st.multiselect("Workloads", workloads, default=workloads)

    st.header("Scoring Weights")
    w_price = st.slider("Price importance", 0.0, 1.0, 0.4, 0.05)
    w_cpu = st.slider("CPU importance", 0.0, 1.0, 0.3, 0.05)
    w_mem = st.slider("Memory importance", 0.0, 1.0, 0.2, 0.05)
    w_net = st.slider("Network importance", 0.0, 1.0, 0.1, 0.05)

subset = df[
    df["region"].isin(selected_regions) & df["workload_tag"].isin(selected_workloads)
].copy()

if subset.empty:
    st.warning("No instances match your filters.")
    st.stop()

w_sum = w_price + w_cpu + w_mem + w_net
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

best = ranked.iloc[0]
st.success(
    f"Top recommendation: **{best['instance_type']}** in **{best['region']}** at "
    f"**${best['price_usd_hour']:.3f}/hr** (score {best['composite_score']:.3f})"
)

col1, col2 = st.columns([1.1, 1])

with col1:
    st.subheader("Top Candidates")
    st.dataframe(
        ranked[
            [
                "instance_type",
                "family",
                "region",
                "workload_tag",
                "vcpus",
                "memory_gib",
                "network_score",
                "price_usd_hour",
                "composite_score",
            ]
        ].head(20),
        use_container_width=True,
        hide_index=True,
    )

with col2:
    st.subheader("Price vs Performance")
    ranked["perf_index"] = (
        ranked["vcpus"] * 0.45 + ranked["memory_gib"] * 0.35 + ranked["network_score"] * 0.2
    )
    fig = px.scatter(
        ranked,
        x="price_usd_hour",
        y="perf_index",
        color="region",
        size="composite_score",
        hover_name="instance_type",
        hover_data=["workload_tag", "vcpus", "memory_gib", "network_score"],
        title="Lower-left is cheaper, upper-right is stronger",
    )
    st.plotly_chart(fig, use_container_width=True)
