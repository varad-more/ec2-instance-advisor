# EC2 Instance Advisor

Interactive static web app to compare AWS EC2 instances by **price vs performance** and quickly shortlist the best fit for your workload.

- Live app: **http://varadmore.me/ec2-instance-advisor/**
- Repo: `varad-more/ec2-instance-advisor`

---

## What this project does

EC2 Instance Advisor helps you answer: _“Which instance should I choose for my use case and budget?”_

It combines:
- Regional on-demand pricing snapshot
- Instance specs (vCPU, memory, GPU, network)
- Weighted scoring (Price / CPU / Memory / Network / GPU)
- Visual comparison charts + recommendation card
- Monthly/annual cost calculator

---

## Features

- Region and category filters (CPU / GPU / Memory / Storage / General)
- Region pagination controls
- Multi-metric comparison chart (select multiple Y-axis metrics)
- Value/performance visualizations (Plotly)
- Best-fit recommendation + explanation
- Pricing calculator (hours, instance count, optional storage estimate)
- Static deployment (GitHub Pages compatible)

---

## Project structure

```text
.
├── docs/
│   ├── index.html                    # Main static app (HTML/CSS/JS)
│   └── data/
│       └── ec2_aws_snapshot.csv      # Snapshot used by hosted app
├── data/
│   └── ec2_aws_snapshot.csv          # Local copy of snapshot
├── scripts/
│   └── fetch_aws_prices_once.py      # One-time AWS pricing pull script
├── src/                              # Python helpers used in local app/dev flow
└── README.md
```

---

## Local run

```bash
git clone https://github.com/varad-more/ec2-instance-advisor.git
cd ec2-instance-advisor
python3 -m http.server 8080 --directory docs
```

Open: `http://localhost:8080`

> Use an HTTP server (not `file://`) because the app fetches CSV data.

---

## Refresh data (one-time snapshot)

```bash
python3 scripts/fetch_aws_prices_once.py
```

Outputs:
- `data/ec2_aws_snapshot.csv`
- `docs/data/ec2_aws_snapshot.csv`

Current region scope in snapshot script:
- `ap-south-1` (India)
- `us-east-1`, `us-west-2` (US)

---

## Hosting at `https://varadmore.me/projects/ec2-instance-advisor`

Yes — totally possible ✅

You have two clean options:

### Option A (recommended): Host from your main site repo (`varad-more.github.io`)

Since your domain already points there, publish this app as a subpath:

1. In `varad-more.github.io`, create folder:
   - `projects/ec2-instance-advisor/`
2. Copy these files into it:
   - `docs/index.html`
   - `docs/data/ec2_aws_snapshot.csv` → `projects/ec2-instance-advisor/data/ec2_aws_snapshot.csv`
3. Commit + push to the site repo.
4. Open:
   - `https://varadmore.me/projects/ec2-instance-advisor/`

No proxy needed. Super stable.

### Option B: Reverse proxy to existing path (`/ec2-instance-advisor/`)

If app is already served at `/ec2-instance-advisor/`, add a rewrite/proxy rule on your web server so:
- `/projects/ec2-instance-advisor/*` → `/ec2-instance-advisor/*`

This works, but Option A is cleaner for long-term maintenance.

---

## GitHub Pages setup (if needed)

In repo settings:
- Branch: `main`
- Folder: `/docs`

This publishes the static app directly from `docs/`.

---

## Notes

- Data is snapshot-based, not live streaming.
- Prices are on-demand and should be verified before production commitments.
- Great for shortlisting; final sizing should still be validated with workload benchmarks.
