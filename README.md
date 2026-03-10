## EC2 Instance Advisor

Interactive static web app to compare AWS EC2 instances by **price vs. performance** and quickly shortlist the best fit for your workload.

- **Live app**: `http://varadmore.me/ec2-instance-advisor/`
- **Repo**: `varad-more/ec2-instance-advisor`

---

### Why this project exists

Picking EC2 instances is usually a mix of guesswork, tribal knowledge, and dozens of tabs in the AWS console and docs.  
This project tries to answer a single question in a **transparent, reproducible** way:

> **“Given my workload and budget, which EC2 instance families and types should I start with?”**

It combines:

- **Regional on‑demand pricing snapshot** (pulled once via AWS public pricing API)
- **Instance specs** (vCPU, memory, GPU count, a simple network score)
- **Weighted scoring** across **Price / CPU / Memory / Network / GPU**
- **Visual comparison views** (Plotly charts, tables, highlights)
- A **clear recommendation card** with runners‑up and a **cost calculator**

Everything runs as a static site – there is **no live call into AWS** from the browser.

---

## 1. Quick user guide

Use this section as a “how‑to” for people landing on the app for the first time.

### Step 1 – Choose your AWS region

- Use the **AWS Region** dropdown in the hero.
- All prices, availability and rankings are **specific to this region**.
- The hero stats will update to show how many instances and families are available there.

### Step 2 – Explore instance families

- Scroll to **“Understand Instance Families”**.
- Each card explains a family in plain English:
  - What it is optimized for (CPU, memory, storage, GPU, etc.)
  - Typical workloads
  - Example instance types.
- Clicking a card:
  - Filters charts, tables, and recommendations down to that family.
  - Or keep **All families** selected for a broad search.

### Step 3 – Set your priorities

- In the **“Set priorities & drill down”** section you’ll see sliders for:
  - **Price**, **CPU**, **Memory**, **Network**, **GPU**.
- These sliders control **how much the scoring cares about each dimension**:
  - Slide **Price** up if cost is critical.
  - Slide **CPU / Memory / GPU** up if you care more about performance than dollars.
- Use presets like **Balanced**, **Cost‑optimized**, **ML / GPU‑heavy** to get sane starter settings.

### Step 4 – Review the recommendation & runners‑up

- The **Top match** card shows:
  - The **instance type** and family.
  - The **advisor score** (0–100) based on your priorities.
  - Key specs (vCPUs, memory, GPU, network score, region‑specific price).
  - A short **“why this instance”** explanation.
- Underneath, you’ll see **runners‑up**, so you can compare 3–5 strong options instead of the full catalog.

### Step 5 – Use the table & cost calculator for final checks

- The **table view** lets you:
  - Sort / search instances.
  - See normalized scores and raw specs in one place.
- The **cost calculator** takes:
  - Instance type, count, hours per month,
  - Optional EBS + data transfer assumptions,
  - And estimates a **monthly bill** using the same snapshot pricing.

---

## 2. Features at a glance

- **Region and category filters**
  - CPU / GPU / Memory / Storage / General.
  - Instance‑family cards double as an explanation and a filter.
- **Priority sliders + presets**
  - Tune how important Price vs. CPU vs. Memory vs. Network vs. GPU are for _your_ workload.
  - Presets for common patterns (balanced, cost‑focused, ML, performance).
- **Charts & visualizations**
  - Family‑level bar / line charts for cost vs. performance.
  - Score breakdown and architecture reference tables.
- **Top recommendation + transparent scoring**
  - Advisor score out of 100 with a text explanation and breakdown.
  - Runners‑up list so you can compare alternatives quickly.
- **Cost calculator**
  - On‑demand hourly pricing → estimated monthly / yearly cost.
  - Optional storage + data transfer knobs.
- **Static deployment (GitHub Pages‑friendly)**
  - Everything lives under `docs/` and can be hosted from any static site host.

---

## 3. Data & scoring methodology (high‑level)

This section is written for users who want to understand _how_ the scores are produced without reading the entire codebase.

### 3.1 Data source

- Data is pulled from the **official AWS public pricing API** using `scripts/fetch_aws_prices_once.py`.
- For each region and instance type in `TARGET_REGIONS` and `TARGET_TYPES`, the script extracts:
  - On‑demand **Linux hourly price**.
  - **vCPU count**, **memory (GiB)**, **GPU count**, **network performance string**.
  - A coarse **network score** from 1–5 derived from phrases like “Moderate”, “10 Gigabit”, “Very High”.
- The script writes two identical CSVs:
  - `data/ec2_aws_snapshot.csv` (local use)
  - `docs/data/ec2_aws_snapshot.csv` (used by the web app)

### 3.2 Instance categorization

Instances are mapped into categories to make the UI easier to reason about:

- **General**: M/T families and others that don’t obviously skew towards a single resource.
- **CPU**: C family and HPC variants (compute‑optimized, high vCPU‑to‑memory ratio).
- **Memory**: R/X/Z families (high memory‑to‑vCPU ratio).
- **Storage**: I/D/Im families (local NVMe, high IOPS / throughput).
- **GPU**: G/P/Trn/Inf families (accelerated compute).

The `workload_tag` field in the CSV mirrors this at a high level (compute / gpu / memory / storage / general).

### 3.3 Normalization & scoring

For each instance in the current region:

1. **Normalize** each metric (price, vCPUs, memory, network, GPU count) to a 0–1 range so that:
   - The cheapest instance gets a better normalized **price score**.
   - The highest spec instances get better **CPU / Memory / GPU / Network scores**.
2. Apply your **slider weights**:
   - Each slider is interpreted as a percentage weight (0–100).
   - Internally the app normalizes these to sum to 1.0.
3. Compute a **composite score**:
   - \( \text{Score} = w_\text{price} \cdot S_\text{price} + w_\text{cpu} \cdot S_\text{cpu} + \dots \)
4. Sort by composite score (descending) within the selected filters.

The final “Advisor score” you see in the UI is a scaled version of this composite value (0–100).

### 3.4 Limitations

- Prices are a **point‑in‑time snapshot** and will drift from live AWS console prices over time.
- Only **Linux on‑demand, shared tenancy** SKUs are considered (no RIs, SPs, or Windows licensing in the score itself).
- Networking is represented as a coarse ordinal score, not real‑world throughput.
- The tool is designed to **shortlist** strong candidates – you should still benchmark your actual workload.

---

## 4. Project structure

```text
.
├── docs/
│   ├── index.html                    # Main static app (HTML, CSS, JS)
│   ├── styles.css                    # Single-page styling + responsive layout
│   └── data/
│       └── ec2_aws_snapshot.csv      # Snapshot used by hosted app
├── data/
│   └── ec2_aws_snapshot.csv          # Local copy of the same snapshot
├── scripts/
│   └── fetch_aws_prices_once.py      # One-time AWS pricing pull script
└── README.md
```

- There is **no build step**: the browser loads `index.html`, `styles.css`, `plotly.js`, and the CSV.
- All interaction logic (charts, sliders, scoring, routing between sections) lives in inline `<script>` in `docs/index.html`.

---

## 5. Running locally

```bash
git clone https://github.com/varad-more/ec2-instance-advisor.git
cd ec2-instance-advisor
python3 -m http.server 8080 --directory docs
```

Then open `http://localhost:8080` in your browser.

> Use an HTTP server (not `file://`) because the app fetches CSV data via `fetch()`.

---

## 6. Refreshing the pricing snapshot

To refresh the CSV with the latest AWS on‑demand prices for the selected regions and instance types:

```bash
python3 scripts/fetch_aws_prices_once.py
```

This writes:

- `data/ec2_aws_snapshot.csv`
- `docs/data/ec2_aws_snapshot.csv`

Regions covered in `TARGET_REGIONS` (see the script for the current full list) include:

- North America: `us-east-1`, `us-east-2`, `us-west-1`, `us-west-2`, `ca-central-1`, `ca-west-1`, `mx-central-1`
- Europe: `eu-west-1`, `eu-west-2`, `eu-west-3`, `eu-central-1`, `eu-central-2`, `eu-north-1`, `eu-south-1`, `eu-south-2`
- Asia Pacific: `ap-south-1`, `ap-south-2`, `ap-southeast-1`, `ap-southeast-2`, `ap-southeast-3`, `ap-southeast-4`, `ap-northeast-1`, `ap-northeast-2`, `ap-northeast-3`, `ap-east-1`
- Others: `sa-east-1`, `me-south-1`, `me-central-1`, `af-south-1`, `il-central-1`

---

## 7. Hosting / deployment

The project is designed for **static hosting**.

### 7.1 GitHub Pages

In repo settings:

- **Branch**: `main`
- **Folder**: `/docs`

GitHub Pages will then serve the app from:

- `https://<username>.github.io/ec2-instance-advisor/` (or your custom domain).

### 7.2 Hosting under `https://varadmore.me/projects/ec2-instance-advisor`

If your main site repo is `varad-more.github.io`, one simple setup is:

1. In `varad-more.github.io`, create:
   - `projects/ec2-instance-advisor/`
2. Copy from this repo:
   - `docs/index.html`
   - `docs/styles.css`
   - `docs/data/ec2_aws_snapshot.csv` → `projects/ec2-instance-advisor/data/ec2_aws_snapshot.csv`
3. Commit + push.
4. Open:
   - `https://varadmore.me/projects/ec2-instance-advisor/`

Alternatively, if the app is already served at `/ec2-instance-advisor/`, your web server can proxy:

- `/projects/ec2-instance-advisor/*` → `/ec2-instance-advisor/*`

---

## 8. Design & UX notes

This repo intentionally includes quite a bit of UI polish so it feels like a **product**, not just a demo:

- **Mobile‑first layout**
  - Multiple breakpoints for grids, cards, charts, and tables.
  - Horizontal scrolling only where dense data demands it (e.g., the main table).
- **Guided funnel**
  - The app reads roughly as: **Families → Aggregates → Architecture → Priorities → Recommendation → Browse → Cost → Methodology**.
- **Copy‑friendly recommendation**
  - A “copy recommendation” button lets you paste the suggested instance + rationale into tickets, docs, or chats.

If you extend the app, try to keep new features aligned with these principles: **clear steps, transparent scoring, and workload‑first language.**

---

## 9. Typical workload mapping (cheat‑sheet)

Use this as a quick reference when you are not sure where to start.

| Workload Type | Recommended Family | Characteristics |
| --- | --- | --- |
| Web & app servers | General Purpose (M/T) | Balanced CPU and memory. Use T‑series (burstable) for dev/test and M‑series for steady production traffic. |
| High‑traffic APIs & HPC | Compute Optimized (C) | High vCPU‑to‑memory ratio. Great for scientific modeling, batch processing, and dedicated game servers. |
| In‑memory databases | Memory Optimized (R/X) | High RAM‑to‑vCPU ratio (8:1 or higher). Ideal for Redis, SAP HANA, and real‑time analytics. |
| NoSQL & data warehousing | Storage Optimized (I/D) | Local NVMe SSDs for millions of low‑latency IOPS. Good for MongoDB, Cassandra, logging, and OLAP stores. |
| AI training & rendering | Accelerated (P/G/Trn/Inf) | GPU or accelerator‑heavy. Use P‑series for deep learning training, G‑series for inference / graphics, Trn/Inf for AWS‑native ML workloads. |

---

## 10. Contributing / extending

Ideas for future improvements:

- Add more **workload templates** that automatically set families + weights.
- Integrate a simple **“guided wizard”** that asks a few natural‑language questions and sets the sliders for you.
- Support more pricing models (RIs, Savings Plans) as toggleable views.
- Persist **user notes** per instance so people can record why they picked a given type.

If you open a PR, briefly describe:

- What UX or understanding problem it solves.
- Whether it changes the scoring behavior.
- Any new assumptions about pricing or regions.

This helps keep the advisor opinionated but predictable.


## Analytics setup (same style as varadmore.me)

This project now supports optional GA4-style tracking in the static app.

### Enable Google Analytics

Set a GA4 measurement id in one of these ways:

1. Global runtime variable in `docs/index.html` host page:

```html
<script>
  window.EC2_ADVISOR_GA4_ID = "G-XXXXXXXXXX";
</script>
```

2. Or from browser console/localStorage for quick testing:

```js
localStorage.setItem('ec2AdvisorGaId', 'G-XXXXXXXXXX');
location.reload();
```

### Tracked events

- `page_view`
- `ui_click` for key CTA/preset buttons
- `ui_change` for key filters and weight controls

If GA id is not configured, analytics silently stays disabled.
