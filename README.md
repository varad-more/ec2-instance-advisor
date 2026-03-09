# EC2 Instance Advisor

A **zero-dependency static web app** for finding the best-fit AWS EC2 instance for your workload.
Compare on-demand pricing across **24 AWS regions**, rank 42+ instance types by a weighted composite score, and explore interactive visualisations — all in a single HTML file.

Live demo → **[varadmore.me/ec2-instance-advisor/](http://varadmore.me/ec2-instance-advisor/)**

---

## Features

| | |
|---|---|
| **6-step guided funnel** | Understand families → compare → set weights → get recommendation → browse → estimate cost |
| **24 AWS regions** | All major regions across US, EU, AP, SA, ME & Africa |
| **42+ instance types** | c7g, m7g, r7g, g5, i4i, t3, m6i, c6g, … |
| **Weighted scoring** | Sliders for Price / CPU / Memory / Network / GPU |
| **Interactive charts** | Family comparison bar, performance radar, cost trend, value-map scatter (Plotly.js) |
| **Best-fit explainer** | Animated score ring + plain-English reasoning card |
| **Cost estimator** | Monthly cost calculator for up to 4 instances side-by-side |
| **Responsive UI** | Works on desktop & mobile; step-jump nav + back-to-top |

---

## Project Structure

```
.
├── docs/                        # Static web app (served via GitHub Pages)
│   ├── index.html               # Single-file app (HTML + CSS + JS + Plotly)
│   └── data/
│       └── ec2_aws_snapshot.csv # Pricing & metadata snapshot (946 rows)
├── data/
│   └── ec2_aws_snapshot.csv     # Mirror of docs/data/ (for local scripts)
├── scripts/
│   └── fetch_aws_prices_once.py # One-time AWS Price List fetcher
└── README.md
```

---

## Running Locally

No build step, no dependencies — just a Python standard-library HTTP server:

```bash
# Clone the repo
git clone https://github.com/varadmore/ec2-instance-advisor.git
cd ec2-instance-advisor

# Serve the docs/ folder
python3 -m http.server 8080 --directory docs
```

Open **[http://localhost:8080](http://localhost:8080)** in your browser.

> **Why a server?** The app fetches `data/ec2_aws_snapshot.csv` via `fetch()`, which requires HTTP (not `file://`).

---

## Refreshing Pricing Data

The CSV snapshot was generated from the [AWS Price List API](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/price-changes.html).
To regenerate it (pulls live data for `us-east-1`, `us-west-2`, `ap-south-1`):

```bash
python3 scripts/fetch_aws_prices_once.py
```

Output files updated:
- `data/ec2_aws_snapshot.csv`
- `docs/data/ec2_aws_snapshot.csv`

> The script fetches the AWS pricing JSON index (~500 MB per region), so expect a few minutes to complete.
> No AWS credentials required — the Price List API is public.

---

## GitHub Pages Deployment

Enable GitHub Pages in your repo settings:
- **Source:** `main` branch, `/docs` folder

The app will be available at `https://<your-username>.github.io/ec2-instance-advisor/`
(or a custom domain if configured — see [varadmore.me/ec2-instance-advisor/](http://varadmore.me/ec2-instance-advisor/)).

---

## How to Pick an EC2 Instance

1. **Identify workload shape**
   - CPU-heavy (builds, APIs, batch encoding) → `c` family (CPU instances)
   - ML / AI / graphics → `g`, `p`, `trn`, `inf` families (GPU instances)
   - Large in-memory datasets / caches → `r` family (Memory instances)
   - High-throughput / low-latency disk → `i`, `d`, `h` families (Storage instances)
   - Mixed / general purpose → `t`, `m` families (General instances)

2. **Pick your region first** — choose the region closest to your users or data to minimise latency and data-transfer costs.

3. **Tune the weight sliders** — raise Price weight for cost-sensitive workloads; raise CPU / Memory / GPU weights for performance-sensitive ones.

4. **Read the Value Map** — top-left quadrant (low price, high score) is the sweet spot.

5. **Benchmark before committing** — run a representative load test and check CloudWatch utilisation before locking in an instance type.

---

## Data Notes

- Prices are **on-demand Linux/UNIX, Shared tenancy** — no Spot or Reserved pricing.
- Regional prices use verified multipliers relative to `us-east-1` baselines; spot-check against the [AWS Pricing Calculator](https://calculator.aws/) for production decisions.
- The snapshot covers a curated set of modern instance families (Graviton3, Intel Ice Lake, AMD, GPU).
