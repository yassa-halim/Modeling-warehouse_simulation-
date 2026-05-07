"""
simulation/warehouse.py — Multi-Warehouse Simulation Runner
============================================================
Runs simulation per warehouse for products that appear in multiple locations.
"""

from simulation.engine import InventorySimulator


def run_per_warehouse(products: list, max_products: int = 30,
                      horizon: int = None, holding_cost: float = None,
                      ordering_cost: float = None) -> list:
    """
    For each product that appears in multiple warehouses, run EOQ simulation
    per warehouse and return per-warehouse KPI rows.
    """
    rows = []
    kwargs = dict(horizon=horizon, holding_cost=holding_cost,
                  ordering_cost=ordering_cost)

    for p in products[:max_products]:
        warehouses = p.get("warehouses_used", [p.get("primary_warehouse_id", "?")])
        n_wh = len(warehouses)

        for wh_id in warehouses:
            wh_product = dict(p)
            if n_wh > 1:
                wh_product["avg_retail_sales"]   = p["avg_retail_sales"]   / n_wh
                wh_product["std_retail_sales"]   = p["std_retail_sales"]   / n_wh
                wh_product["total_inbound_qty"]  = p["total_inbound_qty"]  / n_wh
                wh_product["total_adjustment_qty"] = p.get("total_adjustment_qty", 0) / n_wh

            res = InventorySimulator(wh_product, "EOQ", **kwargs).run()
            rows.append({
                "product_id":    p["product_id"],
                "product_name":  p["product_name"][:35],
                "warehouse_id":  wh_id,
                "fill_rate":     res["fill_rate"],
                "service_level": res["service_level"],
                "stockout_orders": res["stockout_orders"],
                "total_cost":    res["total_cost"],
                "avg_inventory": res["avg_inventory"],
                "replenishments":res["replenishments"],
            })

    return rows
