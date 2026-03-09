# EC2 Instance Advisor

Find the best AWS EC2 instance for your use case by comparing:
- **Region-wise on-demand prices**
- **Performance profile** (vCPU, memory, network baseline)
- **Workload fit** (general, compute, memory)

This project provides a simple scoring engine + Streamlit UI to guide users toward the best-fit instance based on their priorities.

## Features

- Region + workload filters
- Weight sliders (price vs CPU vs memory vs network)
- Composite score ranking
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
