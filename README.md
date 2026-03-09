# EC2 Instance Advisor

Find the best AWS EC2 instance for your use case by comparing:
- **Region-wise on-demand prices**
- **Performance profile** (vCPU, memory, network baseline)
- **Workload fit** (general, compute, memory)

This project provides a simple scoring engine + Streamlit UI to guide users toward the best-fit instance based on their priorities.

## Features

- Region + instance category filters (CPU/GPU/Memory/Storage/General)
- Weight sliders (price vs CPU vs memory vs network)
- Composite score ranking
- Automatic best-fit explainer card (why this instance is recommended)
- Built-in instance-type guide that explains where each category fits
- Interactive scatter plot (price vs performance)
- Quick recommendations and top candidates table

## Project Structure

```
.
├── app.py
├── data/
│   └── ec2_samples.csv
├── src/
│   ├── __init__.py
│   ├── advisor.py
│   └── loaders.py
├── requirements.txt
└── README.md
```

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open the URL shown by Streamlit (usually `http://localhost:8501`).

## Data Notes

- `data/ec2_samples.csv` includes sample EC2 instance metadata + regional pricing.
- Prices are **illustrative** for MVP/demo and should be refreshed before production use.

## Next Steps

- Add automated pricing refresh from AWS Price List API
- Add Spot price + reserved instance support
- Add architecture filters (x86/ARM)
- Add storage performance metrics (EBS throughput)


## GitHub Pages Hosting

This repo now includes a static web app at `docs/index.html` so it can be hosted on **GitHub Pages**.

Once Pages is enabled for this repo (source: `main` branch, `/docs`), the app is available at:

`http://varadmore.me/ec2-instance-advisor/`


## How to Select an EC2 Instance for Your Needs

A practical method:

1. **Identify workload shape**
   - CPU-heavy (builds, APIs, encoding) → CPU instances
   - ML/AI or graphics workloads → GPU instances
   - Big caches / in-memory databases → Memory instances
   - High disk throughput / low latency storage tasks → Storage instances
   - Mixed/general workloads → General instances

2. **Select region first**
   Pick the closest region to users/data to reduce latency and transfer costs.

3. **Set priorities with weights**
   Increase price weight for cost-sensitive workloads; increase CPU/memory/network/GPU weights for performance-sensitive workloads.

4. **Interpret the plot correctly**
   - **X-axis:** hourly cost (USD/hr)
   - **Y-axis:** performance index (derived from CPU, memory, network, GPU)
   - Better value usually appears where performance is high for acceptable price.

5. **Benchmark before committing**
   Always run a small production-like load test and monitor utilization before finalizing instance type.
