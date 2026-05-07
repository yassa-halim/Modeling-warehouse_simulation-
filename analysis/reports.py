"""
analysis/reports.py — Report Generator
========================================
Generates Markdown reports and CSV exports from inventory flow
aggregations and DES simulation results.
"""

import csv
import io
from datetime import datetime


# ─────────────────────────────────────────────────────────────────────────
# Aggregate KPIs
# ─────────────────────────────────────────────────────────────────────────

def compute_aggregate_kpis(policy_results: list) -> dict:
    """Compute fleet-level KPIs from a list of per-product sim results."""
    n = len(policy_results)
    if n == 0:
        return {k: 0 for k in ["fill_rate", "service_level", "stockout_rate",
                                "total_cost", "total_holding_cost", "total_ordering_cost"]}

    return {
        "fill_rate":            sum(r["fill_rate"]      for r in policy_results) / n,
        "service_level":        sum(r["service_level"]  for r in policy_results) / n,
        "stockout_rate":        sum(r["stockout_rate"]  for r in policy_results) / n,
        "total_cost":           sum(r["total_cost"]     for r in policy_results),
        "total_holding_cost":   sum(r.get("holding_cost", 0) for r in policy_results),
        "total_ordering_cost":  sum(r.get("ordering_cost", 0) for r in policy_results),
    }


# ─────────────────────────────────────────────────────────────────────────
# Reorder Recommendations
# ─────────────────────────────────────────────────────────────────────────

def get_reorder_recommendations(products: list,
                                 sim_results: dict = None,
                                 top_n: int = 15) -> list:
    """Generate actionable reorder recommendations."""
    recs = []
    for p in products:
        net       = p.get("net_qty", 0)
        avg_daily = p.get("avg_outbound_qty", 1)
        days_left = net / avg_daily if avg_daily > 0 else 999

        if days_left < 7:
            urgency = "🔴 HIGH"
            order   = round(avg_daily * 30)
        elif days_left < 14:
            urgency = "🟡 MEDIUM"
            order   = round(avg_daily * 21)
        else:
            urgency = "🟢 LOW"
            order   = round(avg_daily * 14)

        recs.append({
            "product_name":  p["product_name"][:40],
            "sku":           p.get("sku", ""),
            "warehouse":     p.get("primary_warehouse_name", "")[:25],
            "net_qty":       round(net, 1),
            "days_coverage": round(days_left, 1),
            "urgency":       urgency,
            "suggested_order_qty": order,
            "unit_of_measure": p.get("unit_of_measure", ""),
        })

    order_map = {"🔴 HIGH": 0, "🟡 MEDIUM": 1, "🟢 LOW": 2}
    recs.sort(key=lambda x: (order_map.get(x["urgency"], 9), x["days_coverage"]))
    return recs[:top_n]


# ─────────────────────────────────────────────────────────────────────────
# Text Report
# ─────────────────────────────────────────────────────────────────────────

def generate_text_report(products: list, sim_results: dict = None) -> str:
    """Generate a Markdown report from products and optional sim results."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    n   = len(products)

    total_in  = sum(p.get("total_inbound_qty",  0) for p in products)
    total_out = sum(p.get("total_outbound_qty", 0) for p in products)
    total_adj = sum(p.get("total_adjustment_qty", 0) for p in products)
    total_net = sum(p.get("net_qty", 0) for p in products)
    wh_set    = set(w for p in products for w in p.get("warehouses_used", []))
    unique_skus = len(set(p.get("sku", "") for p in products))

    lines = [
        "# 📦 Warehouse Inventory Flow — Simulation Report",
        f"**Generated:** {now}",
        "",
        "---",
        "## 1. Dataset Summary",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Total Products | {n:,} |",
        f"| Unique SKUs | {unique_skus:,} |",
        f"| Active Warehouses | {len(wh_set):,} |",
        f"| Total Inbound Qty | {total_in:,.0f} |",
        f"| Total Outbound Qty | {total_out:,.0f} |",
        f"| Total Adjustments | {total_adj:,.0f} |",
        f"| Net Inventory Position | {total_net:,.0f} |",
        "",
    ]

    # ABC summary
    from analysis.abc import classify_abc, get_abc_summary
    classified = classify_abc(list(products))
    abc = get_abc_summary(classified)
    lines += [
        "## 2. ABC Classification",
        "| Class | Products | Volume % | Strategy |",
        "|---|---|---|---|",
        f"| A (Critical) | {abc['A']['count']} | {abc['A']['volume_pct']:.1f}% | High-frequency review |",
        f"| B (Important) | {abc['B']['count']} | {abc['B']['volume_pct']:.1f}% | Periodic review |",
        f"| C (Low-volume) | {abc['C']['count']} | {abc['C']['volume_pct']:.1f}% | Min stock levels |",
        "",
    ]

    # Top 10 by outbound
    lines += [
        "## 3. Top 10 Products by Outbound Volume",
        "| Rank | Product | SKU | Warehouse | Outbound Qty | ABC |",
        "|---|---|---|---|---|---|",
    ]
    for i, p in enumerate(products[:10], 1):
        cls = p.get("abc_class", "?")
        lines.append(
            f"| {i} | {p['product_name'][:30]} | {p.get('sku','')} "
            f"| {p.get('primary_warehouse_name','')[:20]} "
            f"| {p['total_outbound_qty']:,.0f} | {cls} |"
        )
    lines.append("")

    # Simulation results
    if sim_results:
        kA = compute_aggregate_kpis(sim_results.get("policy_a", []))
        kB = compute_aggregate_kpis(sim_results.get("policy_b", []))
        kC = compute_aggregate_kpis(sim_results.get("policy_c", []))
        best = min([("FOQ", kA["total_cost"]),
                    ("EOQ", kB["total_cost"]),
                    ("JIT", kC["total_cost"])],
                   key=lambda x: x[1])

        lines += [
            "## 4. Simulation Results — FOQ vs EOQ vs JIT",
            "| KPI | FOQ | EOQ | JIT |",
            "|---|---|---|---|",
            f"| Fill Rate | {kA['fill_rate']:.1%} | {kB['fill_rate']:.1%} | {kC['fill_rate']:.1%} |",
            f"| Service Level | {kA['service_level']:.1%} | {kB['service_level']:.1%} | {kC['service_level']:.1%} |",
            f"| Stockout Rate | {kA['stockout_rate']:.1%} | {kB['stockout_rate']:.1%} | {kC['stockout_rate']:.1%} |",
            f"| Total Cost $ | {kA['total_cost']:,.0f} | {kB['total_cost']:,.0f} | {kC['total_cost']:,.0f} |",
            "",
            f"> ✅ **Recommended Policy: {best[0]}** — Lowest total cost (${best[1]:,.0f})",
            "",
        ]

    # Reorder recommendations
    recs = get_reorder_recommendations(products)
    lines += [
        "## 5. Reorder Recommendations",
        "| Product | SKU | Warehouse | Net Qty | Days Cover | Urgency | Suggested Order |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in recs:
        lines.append(
            f"| {r['product_name']} | {r['sku']} | {r['warehouse']} "
            f"| {r['net_qty']:,.0f} | {r['days_coverage']:.0f} days "
            f"| {r['urgency']} | {r['suggested_order_qty']:,} {r['unit_of_measure']} |"
        )

    lines += ["", "---", "_Report auto-generated by Warehouse Flow Simulation Engine_"]
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────
# CSV Export
# ─────────────────────────────────────────────────────────────────────────

def export_simulation_csv(sim_results: dict) -> str:
    """Return a CSV string of all policy results combined."""
    fields = [
        "policy", "item_id", "item_name", "fill_rate", "service_level",
        "stockout_rate", "total_demand", "total_sold", "stockout_orders",
        "replenishments", "avg_inventory", "total_cost", "holding_cost", "ordering_cost",
    ]
    policy_map = {"policy_a": "FOQ", "policy_b": "EOQ", "policy_c": "JIT"}
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for key, label in policy_map.items():
        for r in sim_results.get(key, []):
            row = dict(r)
            row["policy"] = label
            writer.writerow(row)
    return output.getvalue()
