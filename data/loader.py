"""
data/loader.py — CSV Reader & Aggregator
=========================================
Reads warehouse-inventory-flow-dataset.csv using built-in csv module only.
NO pandas · NO numpy · NO MongoDB.

Aggregation logic:
    - Group by product_id
    - inbound     → cumulative inbound stock
    - outbound    → cumulative outbound (demand proxy)
    - transfer    → counted separately
    - adjustment  → counted separately (shrinkage / audit)
    - avg / std of outbound quantity → used by simulation engine as demand
"""

import csv
import math
import os
from datetime import datetime

from config import CSV_FILE_PATH


# ─────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────

def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(str(value).strip())
    except (ValueError, TypeError):
        return default


def _parse_datetime(value: str):
    """Parse ISO datetime string → datetime object, or None on failure."""
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None


def _resolve_path(filepath=None) -> str:
    if filepath is None:
        filepath = CSV_FILE_PATH
    if not os.path.isabs(filepath):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filepath = os.path.join(project_root, filepath)
    return filepath


# ─────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────

def load_and_aggregate_from_csv(filepath=None, progress_callback=None) -> list:
    """
    Stream-read the inventory flow CSV and return one aggregated dict per
    unique product_id, exploiting ALL 23 columns.

    Returns list[dict] sorted by total_outbound_qty descending.

    Raises:
        FileNotFoundError  if CSV is missing.
        ValueError         if CSV has no data rows.
    """
    filepath = _resolve_path(filepath)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"CSV not found: {filepath}")

    acc: dict = {}      # product_id → running stats
    rows_read = 0

    with open(filepath, mode="r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)

        for raw in reader:
            rows_read += 1

            # ── Identity ─────────────────────────────────────────────
            product_id   = str(raw.get("product_id",   "")).strip()
            product_name = str(raw.get("product_name", "")).strip()
            sku          = str(raw.get("sku",          "")).strip()
            uom          = str(raw.get("unit_of_measure", "")).strip()

            if not product_id:
                continue

            # ── Location ─────────────────────────────────────────────
            wh_id      = str(raw.get("warehouse_id",   "")).strip()
            wh_name    = str(raw.get("warehouse_name", "")).strip()
            wh_city    = str(raw.get("warehouse_city",    "")).strip()
            wh_state   = str(raw.get("warehouse_state",   "")).strip()
            wh_country = str(raw.get("warehouse_country", "")).strip()

            # ── Movement ─────────────────────────────────────────────
            movement_type  = str(raw.get("movement_type", "")).strip().lower()
            qty            = _safe_float(raw.get("quantity", 0))
            movement_dt_str= str(raw.get("movement_datetime", "")).strip()
            movement_reason= str(raw.get("movement_reason", "")).strip()

            movement_dt = _parse_datetime(movement_dt_str)

            # ── Init accumulator ─────────────────────────────────────
            if product_id not in acc:
                acc[product_id] = {
                    "product_id": product_id, "product_name": product_name,
                    "sku": sku, "unit_of_measure": uom,
                    "_wh_counts": {}, "_wh_meta": {},
                    "total_inbound_qty": 0.0, "total_outbound_qty": 0.0,
                    "total_transfer_qty": 0.0, "total_adjustment_qty": 0.0,
                    "inbound_events": 0, "outbound_events": 0,
                    "transfer_events": 0, "adjustment_events": 0,
                    "record_count": 0,
                    "_outbound_qty_list": [],
                    "_datetimes": [], "_active_dates": set(),
                    "_reasons": set(), "_warehouses": set(),
                }

            p = acc[product_id]
            p["record_count"] += 1

            # ── Warehouse frequency map ───────────────────────────────
            p["_wh_counts"][wh_id] = p["_wh_counts"].get(wh_id, 0) + 1
            if wh_id not in p["_wh_meta"]:
                p["_wh_meta"][wh_id] = {
                    "name": wh_name, "city": wh_city,
                    "state": wh_state, "country": wh_country,
                }
            p["_warehouses"].add(wh_id)

            # ── Flow accumulation ────────────────────────────────────
            if movement_type == "inbound":
                p["total_inbound_qty"] += qty
                p["inbound_events"]    += 1
            elif movement_type == "outbound":
                p["total_outbound_qty"]   += qty
                p["outbound_events"]      += 1
                p["_outbound_qty_list"].append(qty)
            elif movement_type == "transfer":
                p["total_transfer_qty"] += qty
                p["transfer_events"]    += 1
            elif movement_type == "adjustment":
                p["total_adjustment_qty"] += qty
                p["adjustment_events"]    += 1

            # ── Time & reason tracking ────────────────────────────────
            if movement_dt:
                p["_datetimes"].append(movement_dt)
                p["_active_dates"].add(movement_dt.date())
            if movement_reason:
                p["_reasons"].add(movement_reason)

            if progress_callback and rows_read % 500 == 0:
                progress_callback(rows_read, rows_read)

    if rows_read == 0:
        raise ValueError("CSV file contains no data rows.")

    # ── Post-process ─────────────────────────────────────────────────────
    result = []
    for p in acc.values():

        # primary warehouse
        wh_counts  = p.pop("_wh_counts")
        wh_meta    = p.pop("_wh_meta")
        primary_wh = max(wh_counts, key=wh_counts.get) if wh_counts else ""
        meta       = wh_meta.get(primary_wh, {})
        p["primary_warehouse_id"]      = primary_wh
        p["primary_warehouse_name"]    = meta.get("name", "")
        p["primary_warehouse_city"]    = meta.get("city", "")
        p["primary_warehouse_state"]   = meta.get("state", "")
        p["primary_warehouse_country"] = meta.get("country", "")

        # demand stats from outbound
        out_list = p.pop("_outbound_qty_list")
        n_out    = len(out_list)
        avg_out  = p["total_outbound_qty"] / n_out if n_out > 0 else 1.0
        std_out  = (
            math.sqrt(sum((x - avg_out) ** 2 for x in out_list) / (n_out - 1))
            if n_out > 1 else max(avg_out * 0.15, 0.1)
        )
        p["avg_outbound_qty"] = round(avg_out, 4)
        p["std_outbound_qty"] = round(std_out, 4)

        # net inventory
        p["net_qty"] = round(
            p["total_inbound_qty"] - p["total_outbound_qty"] - p["total_adjustment_qty"], 2,
        )

        # time profile
        dts = p.pop("_datetimes")
        if dts:
            p["first_movement_dt"] = min(dts).strftime("%Y-%m-%d %H:%M")
            p["last_movement_dt"]  = max(dts).strftime("%Y-%m-%d %H:%M")
        else:
            p["first_movement_dt"] = ""
            p["last_movement_dt"]  = ""
        p["active_days"] = len(p.pop("_active_dates"))

        # traceability
        p["movement_reasons"] = sorted(p.pop("_reasons"))
        p["warehouses_used"]  = sorted(p.pop("_warehouses"))

        # ── Simulation engine aliases ────────────────────────────────
        p["avg_retail_sales"]   = p["avg_outbound_qty"]
        p["std_retail_sales"]   = p["std_outbound_qty"]
        p["total_retail_sales"] = p["total_outbound_qty"]
        p["total_warehouse"]    = p["total_inbound_qty"]
        p["item_id"]   = p["product_id"]
        p["item_name"] = p["product_name"]
        p["item_type"] = p.get("unit_of_measure", "")
        p["supplier"]  = p["primary_warehouse_id"]

        result.append(p)

    result.sort(key=lambda x: x["total_outbound_qty"], reverse=True)

    if progress_callback:
        progress_callback(rows_read, rows_read)

    return result
