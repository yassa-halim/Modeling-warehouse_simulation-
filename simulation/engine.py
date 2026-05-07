"""
============================================================================
simulation/engine.py — Discrete-Event Simulation (DES) Engine
============================================================================
Hand-coded DES engine (NO simpy).

Event Types:
    CUSTOMER_ORDER    — Daily demand (Poisson)
    INVENTORY_REVIEW  — End-of-day stock check + reorder trigger
    SHIPMENT_ARRIVAL  — Replenishment after lead-time
    ADJUSTMENT        — Daily shrinkage (from adjustment qty in data)

Policies:
    FOQ — Fixed Order Quantity
    EOQ — Economic Order Quantity with safety stock
    JIT — Just-In-Time: order only when stockout imminent
============================================================================
"""

import math
import random

from config import (
    SIMULATION_HORIZON_DAYS,
    INITIAL_STOCK_MULTIPLIER,
    LEAD_TIME_MEAN,
    LEAD_TIME_STD,
    MIN_LEAD_TIME,
    FOQ_ORDER_SIZE,
    FOQ_REORDER_POINT_DAYS,
    JIT_SAFETY_DAYS,
    SERVICE_LEVEL_Z,
    DEFAULT_HOLDING_COST,
    DEFAULT_ORDERING_COST,
)
from simulation.event_queue import Event, MinHeapEventQueue
from simulation.math_utils import (
    normal_variate,
    poisson_variate,
    compute_eoq,
    compute_safety_stock,
    compute_reorder_point,
)


class InventorySimulator:
    """
    Discrete-Event Simulation engine for warehouse inventory management.

    Simulates daily demand, stock reviews, and shipment arrivals for
    a single product over SIMULATION_HORIZON_DAYS. Supports two policies:
    'FOQ' (Fixed Order Quantity) and 'EOQ' (Economic Order Quantity).
    """

    def __init__(self, product, policy="FOQ", horizon=None,
                 holding_cost=None, ordering_cost=None):
        """
        Args:
            product   : dict with item_id, item_name, avg_retail_sales,
                        std_retail_sales, total_inbound_qty,
                        total_adjustment_qty, record_count
            policy    : 'FOQ' | 'EOQ' | 'JIT'
            horizon   : simulation days (overrides config)
            holding_cost / ordering_cost : override config defaults
        """
        self.product  = product
        self.policy   = policy
        self.horizon  = horizon or SIMULATION_HORIZON_DAYS
        self.h_cost   = holding_cost  or DEFAULT_HOLDING_COST
        self.o_cost   = ordering_cost or DEFAULT_ORDERING_COST

        # Daily demand from outbound stats
        avg_out = product.get("avg_retail_sales", 1.0)
        std_out = product.get("std_retail_sales", 0.5)
        self.avg_daily_demand = max(avg_out / 30.0, 0.01)
        self.std_daily_demand = max(std_out / math.sqrt(30.0), 0.01)

        # Daily shrinkage from adjustment data
        total_adj = product.get("total_adjustment_qty", 0.0)
        self.daily_shrinkage = max(total_adj / max(self.horizon, 1), 0.0)

        # Initial inventory — use actual inbound if available
        total_inbound = product.get("total_inbound_qty", 0.0)
        if total_inbound > 0:
            self.inventory = total_inbound
        else:
            self.inventory = max(self.avg_daily_demand * INITIAL_STOCK_MULTIPLIER, 1.0)

        self._setup_policy()

        self.event_queue = MinHeapEventQueue()
        self.clock       = 0.0

        # Metrics
        self.total_demand      = 0
        self.total_sold        = 0
        self.total_orders      = 0
        self.fulfilled_orders  = 0
        self.stockout_orders   = 0
        self.replenishments    = 0
        self.inventory_snapshots = []
        self.pending_orders    = 0
        self.daily_inventory_sum = 0.0
        self.days_recorded     = 0

    def _setup_policy(self):
        """Configure reorder point and order quantity based on policy."""
        if self.policy == "FOQ":
            self.order_qty    = FOQ_ORDER_SIZE
            self.reorder_point = self.avg_daily_demand * FOQ_REORDER_POINT_DAYS
        elif self.policy == "EOQ":
            annual_demand = self.avg_daily_demand * 365.0
            self.order_qty = compute_eoq(
                annual_demand, self.o_cost, self.h_cost
            )
            ss = compute_safety_stock(
                SERVICE_LEVEL_Z, self.std_daily_demand, LEAD_TIME_MEAN
            )
            self.reorder_point = compute_reorder_point(
                self.avg_daily_demand, LEAD_TIME_MEAN, ss
            )
        else:  # JIT
            # Order only when stock falls below JIT_SAFETY_DAYS of demand
            self.reorder_point = self.avg_daily_demand * JIT_SAFETY_DAYS
            # Order enough to cover lead time + safety window
            self.order_qty = max(
                self.avg_daily_demand * (LEAD_TIME_MEAN + JIT_SAFETY_DAYS), 1.0
            )

    def _schedule_daily_orders(self, day):
        """
        Schedule one aggregated demand event per day.

        Draws total daily demand from Poisson(avg_daily_demand), then
        places a single CUSTOMER_ORDER event at a Uniform random time
        within the day. Zero-demand days produce no event.
        """
        daily_qty = poisson_variate(self.avg_daily_demand)
        if daily_qty <= 0:
            return

        order_time = day + random.uniform(0.0, 0.99)
        self.event_queue.push(
            Event(order_time, "CUSTOMER_ORDER", {"qty": daily_qty})
        )

    def _schedule_daily_review(self, day):
        """Schedule end-of-day inventory review at time = day + 0.999."""
        self.event_queue.push(
            Event(day + 0.999, "INVENTORY_REVIEW", {"day": day})
        )

    def _place_replenishment(self):
        """Place a replenishment order — shipment arrives after lead time."""
        lead_time = normal_variate(LEAD_TIME_MEAN, LEAD_TIME_STD)
        lead_time = max(lead_time, MIN_LEAD_TIME)
        arrival = self.clock + lead_time

        self.event_queue.push(
            Event(arrival, "SHIPMENT_ARRIVAL", {"qty": self.order_qty})
        )
        self.replenishments += 1
        self.pending_orders += 1

    def _handle_customer_order(self, event):
        """Process one daily demand event."""
        qty = event.data.get("qty", 1)
        self.total_demand += qty
        self.total_orders += 1   # one order event = one demand occurrence

        if self.inventory >= qty:
            self.inventory -= qty
            self.total_sold   += qty
            self.fulfilled_orders += 1
        else:
            # Partial fill: sell available stock, remainder is a lost sale
            sold = max(self.inventory, 0)
            self.total_sold   += sold
            self.inventory     = 0
            self.stockout_orders += 1

    def _handle_inventory_review(self, event):
        """End-of-day inventory check. Reorder if below reorder point."""
        self.daily_inventory_sum += self.inventory
        self.days_recorded += 1
        day = event.data.get("day", self.clock)
        self.inventory_snapshots.append({
            "day": int(day),
            "inventory": round(self.inventory, 2),
        })

        if self.inventory <= self.reorder_point and self.pending_orders == 0:
            self._place_replenishment()

    def _handle_shipment_arrival(self, event):
        """Process a shipment arrival — add stock."""
        qty = event.data.get("qty", 0)
        self.inventory += qty
        self.pending_orders = max(self.pending_orders - 1, 0)

    def run(self):
        """Execute the full DES loop over the simulation horizon."""
        for day in range(self.horizon):
            self._schedule_daily_orders(day)
            self._schedule_daily_review(day)
            # Schedule daily shrinkage if product has adjustment data
            if self.daily_shrinkage > 0:
                self.event_queue.push(
                    Event(day + 0.5, "ADJUSTMENT",
                          {"qty": self.daily_shrinkage})
                )

        while not self.event_queue.is_empty():
            event = self.event_queue.pop()
            self.clock = event.time

            if event.event_type == "CUSTOMER_ORDER":
                self._handle_customer_order(event)
            elif event.event_type == "INVENTORY_REVIEW":
                self._handle_inventory_review(event)
            elif event.event_type == "SHIPMENT_ARRIVAL":
                self._handle_shipment_arrival(event)
            elif event.event_type == "ADJUSTMENT":
                # Shrinkage: reduce inventory, never below 0
                self.inventory = max(self.inventory - event.data["qty"], 0)

        return self._compile_results()

    def _compile_results(self):
        """Compile simulation metrics into a results dictionary."""
        avg_inv = (self.daily_inventory_sum / self.days_recorded
                   if self.days_recorded > 0 else 0)
        fill_rate = (self.total_sold / self.total_demand
                     if self.total_demand > 0 else 1.0)
        service_level = (self.fulfilled_orders / self.total_orders
                         if self.total_orders > 0 else 1.0)
        stockout_rate = (self.stockout_orders / self.total_orders
                         if self.total_orders > 0 else 0.0)

        holding_cost  = avg_inv * (self.h_cost / 365.0) * self.horizon
        ordering_cost = self.replenishments * self.o_cost
        total_cost = holding_cost + ordering_cost

        return {
            "item_id": self.product.get("item_id", ""),
            "item_name": self.product.get("item_name", ""),
            "policy": self.policy,
            "horizon_days": self.horizon,
            "total_demand": self.total_demand,
            "total_sold": self.total_sold,
            "total_orders": self.total_orders,
            "fulfilled_orders": self.fulfilled_orders,
            "stockout_orders": self.stockout_orders,
            "replenishments": self.replenishments,
            "avg_inventory": round(avg_inv, 2),
            "final_inventory": round(self.inventory, 2),
            "fill_rate": round(fill_rate, 4),
            "service_level": round(service_level, 4),
            "stockout_rate": round(stockout_rate, 4),
            "holding_cost": round(holding_cost, 2),
            "ordering_cost": round(ordering_cost, 2),
            "total_cost": round(total_cost, 2),
            "order_qty": round(self.order_qty, 2),
            "reorder_point": round(self.reorder_point, 2),
            "inventory_snapshots": self.inventory_snapshots,
        }


def run_simulation_for_products(
    products,
    max_products=50,
    horizon=None,
    holding_cost=None,
    ordering_cost=None,
    progress_callback=None,
):
    """
    Run DES for a list of products under FOQ, EOQ, and JIT policies.

    Returns:
        dict: {'policy_a': [FOQ results],
               'policy_b': [EOQ results],
               'policy_c': [JIT results]}
    """
    results_a, results_b, results_c = [], [], []

    eligible = [p for p in products if p.get("avg_retail_sales", 0) > 0]
    selected = eligible[:max_products]
    total    = len(selected)

    kwargs = dict(horizon=horizon, holding_cost=holding_cost,
                  ordering_cost=ordering_cost)

    for i, product in enumerate(selected):
        results_a.append(InventorySimulator(product, "FOQ", **kwargs).run())
        results_b.append(InventorySimulator(product, "EOQ", **kwargs).run())
        results_c.append(InventorySimulator(product, "JIT", **kwargs).run())

        if progress_callback:
            progress_callback(i + 1, total)

    return {"policy_a": results_a, "policy_b": results_b, "policy_c": results_c}
