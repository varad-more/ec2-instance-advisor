# EC2 Instance Advisor

An interactive tool to compare AWS EC2 instances by price, performance, and workload fit — and get a transparent, explainable recommendation in minutes.

**[Live App](https://varadmore.me/ec2-instance-advisor/)** · **[Report a Bug](https://github.com/varad-more/ec2-instance-advisor/issues)**

---

## What it does

AWS offers 500+ EC2 instance types. Choosing the right one usually means juggling dozens of console tabs, docs pages, and spreadsheets. This tool answers one question:

> **Given my workload priorities and budget, which EC2 instance should I start with?**

It combines a regional pricing snapshot, instance specs (vCPU, memory, GPU, network), and a weighted scoring model into a single guided workflow — all running as a static site with zero backend.

### Key capabilities

- **Guided 4-phase funnel**: Learn families → Compare specs → Get recommendations → Estimate costs
- **Weighted scoring**: Tune Price / CPU / Memory / Network / GPU priorities with presets (Balanced, Cost, Performance, ML)
- **Interactive charts**: Plotly-powered parallel coordinates, radar, bar, scatter, and line charts
- **Transparent scoring**: Every recommendation includes a breakdown explaining _why_ that instance ranked #1
- **TCO calculator**: Estimate monthly costs across On-Demand, Reserved, and Savings Plan billing models
- **Regional pricing**: Compare prices across 26+ AWS regions
- **Shareable URLs**: Current filters and weights are encoded in the URL hash

---

## Quick start

### Run locally

```bash
git clone https://github.com/varad-more/ec2-instance-advisor.git
cd ec2-instance-advisor
python3 -m http.server 8080 --directory docs
# Open http://localhost:8080
```

> A local HTTP server is required because the app uses `fetch()` to load CSV data (`file://` won't work).

### Refresh pricing data

```bash
python3 scripts/fetch_aws_prices_once.py
```

This pulls current on-demand Linux prices from the AWS public pricing API and writes to both `data/` and `docs/data/`.

---

## How to use

### 1. Pick a region
Use the globe dropdown in the navbar. All scores, prices, and charts update instantly. Arrow keys (`←` / `→`) cycle through regions.

### 2. Explore instance families
The family cards in Phase 1 explain what each category is optimized for. Click a card to filter everything to that family, or keep "All" selected.

### 3. Set your priorities
In the **Top Match** section, use the segment bars to set how much you care about each dimension:
- **Off** / **Low** / **Med** / **High** / **Max** for Price, CPU, Memory, Network, GPU
- Or use presets: press `B` (Balanced), `C` (Cost), `P` (Performance), `M` (ML)

### 4. Review results
The recommendation card shows the #1 match with a score breakdown, runners-up, and a natural-language explanation. Click any row in the Browse table to compare it side-by-side against the top pick.

### 5. Estimate costs
The TCO calculator factors in compute hours, EBS storage, and data egress across three billing models.

---

## Project structure

```
ec2-instance-advisor/
├── docs/                          # Static site (deploy this folder)
│   ├── index.html                 # App: HTML structure + inline JS (~4,400 lines)
│   ├── styles.css                 # All styling + responsive breakpoints (~6,000 lines)
│   ├── data/
│   │   └── ec2_aws_snapshot.csv   # Pricing snapshot (2,571 rows × 10 columns)
│   ├── favicon.svg
│   ├── apple-touch-icon.png
│   ├── ogcard.png                 # Open Graph social card
│   ├── robots.txt
│   ├── sitemap.xml
│   └── .nojekyll                  # Disables Jekyll processing on GitHub Pages
├── data/
│   └── ec2_aws_snapshot.csv       # Local copy (identical to docs/)
├── scripts/
│   └── fetch_aws_prices_once.py   # AWS pricing API pull script (Python 3)
└── README.md
```

### Architecture

The app is a **zero-dependency static SPA** (aside from Plotly.js loaded via CDN):

- **No build step** — open `index.html` in a browser (via HTTP server)
- **No framework** — vanilla HTML/CSS/JS
- **No backend** — all scoring runs client-side
- **Centralized state** — a single `state` object holds all app data; the DOM is never read for state

### Code organization (`index.html` script sections)

| Section | What it does |
|---------|-------------|
| 1. App state & DOM helpers | `state` object, `el()` alias, analytics setup |
| 2. UI constants | Category colors, metric labels, preset definitions |
| 3. Segment-bar widget | Click handlers for the 5-level priority buttons |
| 4. Pricing constants | EBS rates, RI/SP discount multipliers, egress tiers |
| 5. ARCH_MAP | Hardware architecture reference (CPU vendor, ISA, hypervisor per family) |
| 6. REGION_META | Region labels and geographic groupings |
| 7. FAMILY_INFO | Instance category card metadata (icons, descriptions, use cases) |
| 8. Utility helpers | `toast()`, `debounce()`, preset application, animated counters |
| 9. Scroll & nav helpers | `scrollToStep()`, scroll-reveal observer |
| 10. URL hash persistence | `saveHash()`, `loadHash()`, `shareURL()` |
| 11. CSV parser & data helpers | `parseCSV()` (RFC 4180), `rankNorm()`, region sync |
| 12. Render functions | Individual chart/card/table renderers |
| 13. `render()` | Main orchestrator — re-scores and repaints all widgets |
| 14. `boot()` | Entry point — fetch CSV, wire events, first render |

---

## Scoring methodology

The advisor uses **Multi-Criteria Decision Analysis (MCDA)** with rank-based normalization.

### How scores are computed

1. **Filter** instances by region and selected categories
2. **Rank-normalize** each metric to [0, 1] using fractional ranks (not min-max — avoids outlier collapse):
   - **Price Efficiency**: `$/compute_unit` where `compute_units = vCPUs + 0.25×RAM + 4×GPUs` (lower is better, inverse-ranked)
   - **CPU**: ranked by vCPU count
   - **Memory**: ranked by GiB
   - **Network**: ranked by network score (1–5 ordinal)
   - **GPU**: ranked by GPU count
3. **Weighted sum**: `composite = Σ(weight_i × score_i)` where weights come from the user's priority settings, normalized to sum to 1.0
4. **Sort** by composite score (descending) → #1 is the recommendation

### Why rank normalization?

Min-max normalization collapses when a single $32/hr GPU instance sets the price ceiling — every sub-$1 instance gets a price score of ~1.0 and they become indistinguishable. Rank normalization distributes scores uniformly regardless of outliers.

### Limitations

- Prices are a **point-in-time snapshot** — they drift from live AWS pricing over time
- Only **Linux on-demand, shared tenancy** SKUs are scored
- Network is a coarse ordinal score (1–5), not actual throughput
- EBS/egress costs in the TCO calculator use **us-east-1 reference rates** — actual rates vary by region
- This is a **shortlisting tool** — always benchmark your actual workload before committing

---

## Deployment

### GitHub Pages

In repo Settings → Pages:
- **Source**: Deploy from a branch
- **Branch**: `main`, folder: `/docs`

The app will be live at `https://<username>.github.io/ec2-instance-advisor/`.

### Any static host

Copy the contents of `docs/` to your web root. No server-side processing is needed.

---

## Data source

Data is pulled from the [AWS public pricing API](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/index.json) using `scripts/fetch_aws_prices_once.py`.

### CSV schema

| Column | Type | Description |
|--------|------|-------------|
| `instance_type` | string | e.g., `m7g.xlarge` |
| `family` | string | e.g., `Compute optimized` |
| `instance_category` | string | `CPU`, `GPU`, `Memory`, `Storage`, or `General` |
| `region` | string | AWS region code, e.g., `us-east-1` |
| `vcpus` | int | vCPU count |
| `memory_gib` | float | RAM in GiB |
| `network_score` | int | 1–5 ordinal derived from network performance strings |
| `gpu_count` | int | Number of GPUs (0 for non-GPU instances) |
| `price_usd_hour` | float | On-demand hourly price (USD) |
| `workload_tag` | string | High-level category tag |

### Covered regions (26)

**Americas**: us-east-1, us-east-2, us-west-1, us-west-2, ca-central-1, ca-west-1, mx-central-1, sa-east-1
**Europe**: eu-west-1/2/3, eu-central-1/2, eu-north-1, eu-south-1/2
**Asia Pacific**: ap-south-1/2, ap-southeast-1/2/3/4, ap-northeast-1/2/3, ap-east-1
**Middle East & Africa**: me-south-1, me-central-1, af-south-1, il-central-1

---

## Keyboard shortcuts

| Key | Action |
|-----|--------|
| `←` / `→` | Cycle AWS regions |
| `B` | Balanced preset |
| `C` | Cost-optimized preset |
| `P` | Performance preset |
| `M` | ML/GPU-heavy preset |
| `/` | Focus the instance search box |

---

## Analytics (optional)

The app supports optional GA4 tracking. To enable:

```js
// Option 1: Global variable (add before the app script)
window.EC2_ADVISOR_GA4_ID = "G-XXXXXXXXXX";

// Option 2: localStorage (for quick testing)
localStorage.setItem('ec2AdvisorGaId', 'G-XXXXXXXXXX');
```

**Tracked events**: `page_view`, `ui_click` (preset/CTA buttons), `ui_change` (filter/weight controls). Analytics stays fully disabled if no ID is configured.

---

## Workload quick reference

| Workload | Family | Why |
|----------|--------|-----|
| Web servers, microservices | General Purpose (M/T) | Balanced CPU and memory; T-series for burstable dev/test |
| High-traffic APIs, HPC | Compute Optimized (C) | High vCPU-to-memory ratio for sustained throughput |
| In-memory databases, caches | Memory Optimized (R/X) | 8:1+ RAM-to-vCPU ratio for Redis, SAP HANA, analytics |
| NoSQL, data warehousing | Storage Optimized (I/D) | Local NVMe SSDs for low-latency IOPS |
| ML training, inference | Accelerated (P/G/Trn/Inf) | GPU/accelerator workloads; Trn/Inf for AWS ML silicon |

---

## Contributing

If you open a PR, briefly describe:
- What UX or understanding problem it solves
- Whether it changes scoring behavior
- Any new pricing or region assumptions

Ideas for future work:
- Guided wizard (questions → auto-set weights)
- RI / Savings Plan pricing toggles in scoring
- Column visibility toggle in the Browse table
- Dark mode

---

## License

This project is not affiliated with, endorsed by, or sponsored by Amazon Web Services. EC2 and AWS are trademarks of Amazon.com, Inc. Pricing data comes from publicly available AWS APIs.

Built by [Varad More](https://varadmore.me).
