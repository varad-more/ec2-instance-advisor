#!/usr/bin/env python3
"""One-time AWS EC2 pricing snapshot fetcher (no dynamic loading in app).

Fetches ALL EC2 instance types from the AWS public pricing API for all
target regions. No hardcoded instance list — every Linux on-demand shared-
tenancy SKU is captured.
"""
from __future__ import annotations
import csv
import json
import re
import sys
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
    "ap-southeast-1", "ap-southeast-2", "ap-southeast-3", "ap-southeast-4", "ap-southeast-5",
    "ap-northeast-1", "ap-northeast-2", "ap-northeast-3", "ap-east-1",
    # South America
    "sa-east-1",
    # Middle East
    "me-south-1", "me-central-1",
    # Africa / Israel
    "af-south-1", "il-central-1",
]
BASE = "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current"


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=120) as r:
        import gzip
        if r.info().get("Content-Encoding") == "gzip":
            data = gzip.decompress(r.read())
        else:
            data = r.read()
        return json.loads(data.decode("utf-8"))


def parse_mem_gib(mem: str) -> float:
    m = re.search(r"([\d,.]+)", (mem or "").replace(",", ""))
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
    """Map network performance string to 1-5 ordinal score."""
    n = (net or "").lower()
    # Extract numeric Gbps if present
    gbps_match = re.search(r"(\d+)\s*(?:gigabit|gbps)", n)
    if gbps_match:
        gbps = int(gbps_match.group(1))
        if gbps >= 100:
            return 5
        if gbps >= 25:
            return 5
        if gbps >= 10:
            return 4
        if gbps >= 5:
            return 3
        return 2
    if "very high" in n or "100 gige" in n:
        return 5
    if "high" in n:
        return 4
    if "moderate" in n:
        return 3
    if "low" in n:
        return 2
    return 3


def category(instance_type: str, gpu_count: int, family_attr: str) -> str:
    """Classify instance into a category using prefix and AWS family attribute."""
    prefix = instance_type.split(".")[0] if "." in instance_type else instance_type

    # GPU / Accelerated — check gpu_count first, then known accelerated prefixes
    if gpu_count > 0:
        return "GPU"
    accel_prefixes = ("g", "p", "trn", "inf", "dl", "vt")
    if any(prefix.startswith(ap) for ap in accel_prefixes):
        return "GPU"

    # Use AWS family attribute as a strong signal
    fam = (family_attr or "").lower()
    if "storage" in fam:
        return "Storage"
    if "memory" in fam:
        return "Memory"
    if "compute" in fam:
        return "CPU"
    if "accelerat" in fam or "machine learning" in fam:
        return "GPU"

    # Fallback to prefix-based classification
    # Compute optimized
    if prefix.startswith(("c", "hpc")):
        return "CPU"
    # Memory optimized
    if prefix.startswith(("r", "x", "z", "u-")):
        return "Memory"
    # Storage optimized
    if prefix.startswith(("i", "d", "h1", "is")):
        return "Storage"
    # General purpose (m, t, mac, a1, etc.)
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
    skipped_regions = []

    for i, region in enumerate(TARGET_REGIONS, 1):
        region_meta = region_idx["regions"].get(region)
        if not region_meta:
            skipped_regions.append(region)
            print(f"  [{i}/{len(TARGET_REGIONS)}] {region} — not found in pricing index, skipping")
            continue

        print(f"  [{i}/{len(TARGET_REGIONS)}] Fetching {region}...", end="", flush=True)
        reg_url = "https://pricing.us-east-1.amazonaws.com" + region_meta["currentVersionUrl"]
        data = fetch_json(reg_url)
        products = data.get("products", {})
        terms_od = data.get("terms", {}).get("OnDemand", {})
        region_count = 0

        for sku, p in products.items():
            a = p.get("attributes", {})
            itype = a.get("instanceType", "")
            if not itype or "." not in itype:
                continue
            if p.get("productFamily") != "Compute Instance":
                continue
            if a.get("operatingSystem") not in ("Linux", "Linux/UNIX"):
                continue
            if a.get("tenancy") != "Shared" or a.get("capacitystatus") != "Used":
                continue
            # Skip pre-installed software SKUs (e.g. SQL Server, RHEL with extras)
            if a.get("preInstalledSw", "NA") not in ("NA", ""):
                continue

            gpu = parse_gpu(a.get("gpu"))
            cat = category(itype, gpu, a.get("instanceFamily", ""))
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
            region_count += 1

        print(f" {region_count} instances")

    # Keep lowest price row per (region, instance_type)
    dedup = {}
    for r in rows:
        k = (r["region"], r["instance_type"])
        if k not in dedup or r["price_usd_hour"] < dedup[k]["price_usd_hour"]:
            dedup[k] = r

    final = sorted(dedup.values(), key=lambda r: (r["region"], r["instance_type"]))

    # Stats
    unique_types = sorted(set(r["instance_type"] for r in final))
    unique_regions = sorted(set(r["region"] for r in final))
    cats = {}
    for r in final:
        cats[r["instance_category"]] = cats.get(r["instance_category"], 0) + 1

    out_csv = Path("docs/data/ec2_aws_snapshot.csv")
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    fields = ["instance_type", "family", "instance_category", "region", "vcpus", "memory_gib", "network_score", "gpu_count", "price_usd_hour", "workload_tag"]
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(final)

    print(f"\nDone! Wrote {len(final)} rows to {out_csv}")
    print(f"  Unique instance types: {len(unique_types)}")
    print(f"  Regions with data:     {len(unique_regions)}")
    print(f"  Categories:            {cats}")
    if skipped_regions:
        print(f"  Skipped regions (not in API): {skipped_regions}")


if __name__ == "__main__":
    main()
