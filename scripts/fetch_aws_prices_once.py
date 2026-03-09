#!/usr/bin/env python3
"""One-time AWS EC2 pricing snapshot fetcher (no dynamic loading in app)."""
from __future__ import annotations
import csv
import json
import re
import urllib.request
from pathlib import Path

TARGET_REGIONS = [
    # North America
    "us-east-1", "us-east-2", "us-west-1", "us-west-2",
    "ca-central-1", "ca-west-1", "mx-central-1",
    # Europe
    "eu-west-1", "eu-west-2", "eu-west-3",
    "eu-central-1", "eu-central-2", "eu-north-1", "eu-south-1", "eu-south-2",
    # Asia Pacific
    "ap-south-1", "ap-south-2",
    "ap-southeast-1", "ap-southeast-2", "ap-southeast-3", "ap-southeast-4",
    "ap-northeast-1", "ap-northeast-2", "ap-northeast-3", "ap-east-1",
    # South America
    "sa-east-1",
    # Middle East
    "me-south-1", "me-central-1",
    # Africa / Israel
    "af-south-1", "il-central-1",
]
TARGET_TYPES = [
    # Burstable
    "t3.small", "t3.medium", "t3.large", "t3.xlarge",
    "t3a.small", "t3a.medium", "t3a.large", "t3a.xlarge",
    "t4g.small", "t4g.medium", "t4g.large", "t4g.xlarge",
    # General Purpose – M family
    "m5.large", "m5.xlarge", "m5.2xlarge", "m5.4xlarge",
    "m6i.large", "m6i.xlarge", "m6i.2xlarge", "m6i.4xlarge",
    "m6a.large", "m6a.xlarge", "m6a.2xlarge",
    "m6g.large", "m6g.xlarge", "m6g.2xlarge",
    "m7i.large", "m7i.xlarge", "m7i.2xlarge",
    "m7a.large", "m7a.xlarge", "m7a.2xlarge",
    "m7g.large", "m7g.xlarge", "m7g.2xlarge",
    "m8g.large", "m8g.xlarge", "m8g.2xlarge", "m8g.4xlarge",
    # Compute Optimized – C family
    "c5.large", "c5.xlarge", "c5.2xlarge", "c5.4xlarge",
    "c6i.large", "c6i.xlarge", "c6i.2xlarge",
    "c6a.large", "c6a.xlarge", "c6a.2xlarge",
    "c6g.large", "c6g.xlarge", "c6g.2xlarge",
    "c7i.large", "c7i.xlarge", "c7i.2xlarge",
    "c7a.large", "c7a.xlarge", "c7a.2xlarge",
    "c7g.large", "c7g.xlarge", "c7g.2xlarge",
    "hpc7g.4xlarge",
    # Memory Optimized – R family
    "r5.large", "r5.xlarge", "r5.2xlarge", "r5.4xlarge",
    "r6i.large", "r6i.xlarge", "r6i.2xlarge",
    "r6a.large", "r6a.xlarge", "r6a.2xlarge",
    "r6g.large", "r6g.xlarge", "r6g.2xlarge",
    "r7i.large", "r7i.xlarge", "r7i.2xlarge",
    "r7a.large", "r7a.xlarge", "r7a.2xlarge",
    "r7g.large", "r7g.xlarge", "r7g.2xlarge",
    "z1d.large", "z1d.xlarge", "z1d.2xlarge",
    "x2idn.16xlarge",
    # Storage Optimized
    "i3.large", "i3.xlarge", "i3.2xlarge",
    "i4i.large", "i4i.xlarge", "i4i.2xlarge",
    "d3.xlarge", "d3.2xlarge",
    "im4gn.large", "im4gn.xlarge",
    # GPU / Accelerated
    "g4dn.xlarge", "g4dn.2xlarge",
    "g5.xlarge", "g5.2xlarge", "g5.4xlarge",
    "g6.xlarge", "g6.2xlarge", "g6.4xlarge",
    "p3.2xlarge",
    "p4d.24xlarge",
    "trn1.2xlarge",
    "inf2.xlarge", "inf2.8xlarge",
]
BASE = "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current"


def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def parse_mem_gib(mem: str) -> float:
    m = re.search(r"([\d.]+)", mem or "")
    return float(m.group(1)) if m else 0.0


def parse_vcpu(v: str) -> int:
    try:
        return int(float(v))
    except Exception:
        return 0


def parse_gpu(g: str) -> int:
    if not g:
        return 0
    m = re.search(r"(\d+)", g)
    return int(m.group(1)) if m else 0


def network_score(net: str) -> int:
    n = (net or "").lower()
    if "very high" in n or "up to 25" in n or "25 gigabit" in n:
        return 5
    if "high" in n or "10 gigabit" in n:
        return 4
    if "moderate" in n or "up to 5" in n:
        return 3
    if "low" in n:
        return 2
    return 3


def category(instance_type: str, gpu_count: int) -> str:
    if gpu_count > 0 or instance_type.startswith(("g", "p", "trn", "inf")):
        return "GPU"
    if instance_type.startswith("hpc"):
        return "CPU"
    if instance_type.startswith("r"):
        return "Memory"
    if instance_type.startswith(("i", "d", "h")):
        return "Storage"
    if instance_type.startswith("c"):
        return "CPU"
    return "General"


def workload_tag(cat: str) -> str:
    return {"CPU": "compute", "GPU": "gpu", "Memory": "memory", "Storage": "storage"}.get(cat, "general")


def first_linux_ondemand_price(terms_od: dict, sku: str) -> float:
    sku_terms = terms_od.get(sku, {})
    for term in sku_terms.values():
        for pd in term.get("priceDimensions", {}).values():
            usd = pd.get("pricePerUnit", {}).get("USD")
            desc = (pd.get("description") or "").lower()
            unit = pd.get("unit")
            if unit == "Hrs" and usd not in (None, "", "0") and "linux" in desc and "on demand" in desc:
                return float(usd)
    # fallback: first hourly non-zero
    for term in sku_terms.values():
        for pd in term.get("priceDimensions", {}).values():
            usd = pd.get("pricePerUnit", {}).get("USD")
            if pd.get("unit") == "Hrs" and usd not in (None, "", "0"):
                return float(usd)
    return 0.0


def main() -> None:
    region_idx = fetch_json(f"{BASE}/region_index.json")
    rows = []

    for region in TARGET_REGIONS:
        region_meta = region_idx["regions"].get(region)
        if not region_meta:
            continue
        reg_url = "https://pricing.us-east-1.amazonaws.com" + region_meta["currentVersionUrl"]
        data = fetch_json(reg_url)
        products = data.get("products", {})
        terms_od = data.get("terms", {}).get("OnDemand", {})

        for sku, p in products.items():
            a = p.get("attributes", {})
            if a.get("instanceType") not in TARGET_TYPES:
                continue
            if p.get("productFamily") != "Compute Instance":
                continue
            if a.get("operatingSystem") not in ("Linux", "Linux/UNIX"):
                continue
            if a.get("tenancy") != "Shared" or a.get("capacitystatus") != "Used":
                continue

            itype = a.get("instanceType")
            gpu = parse_gpu(a.get("gpu"))
            cat = category(itype, gpu)
            price = first_linux_ondemand_price(terms_od, sku)
            if price <= 0:
                continue
            rows.append({
                "instance_type": itype,
                "family": a.get("instanceFamily", ""),
                "instance_category": cat,
                "region": region,
                "vcpus": parse_vcpu(a.get("vcpu", "0")),
                "memory_gib": parse_mem_gib(a.get("memory", "0 GiB")),
                "network_score": network_score(a.get("networkPerformance", "")),
                "gpu_count": gpu,
                "price_usd_hour": round(price, 6),
                "workload_tag": workload_tag(cat),
            })

    # Keep lowest price row per (region, instance_type)
    dedup = {}
    for r in rows:
        k = (r["region"], r["instance_type"])
        if k not in dedup or r["price_usd_hour"] < dedup[k]["price_usd_hour"]:
            dedup[k] = r

    final = sorted(dedup.values(), key=lambda r: (r["region"], r["instance_type"]))

    out_csv = Path("data/ec2_aws_snapshot.csv")
    out_docs = Path("docs/data/ec2_aws_snapshot.csv")
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_docs.parent.mkdir(parents=True, exist_ok=True)

    fields = ["instance_type", "family", "instance_category", "region", "vcpus", "memory_gib", "network_score", "gpu_count", "price_usd_hour", "workload_tag"]
    for path in (out_csv, out_docs):
        with path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(final)

    print(f"Wrote {len(final)} rows to {out_csv} and {out_docs}")


if __name__ == "__main__":
    main()
