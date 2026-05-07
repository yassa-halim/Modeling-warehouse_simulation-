"""
============================================================================
simulation/math_utils.py — Custom Statistical Distributions
============================================================================
Hand-coded distributions using ONLY `random` and `math`. NO numpy/scipy.
Implements: Exponential, Normal (Box-Muller), Poisson (Knuth), EOQ, SS, ROP.
============================================================================
"""

import random
import math


def exponential_variate(lam):
    """Generate Exp(lambda) variate via inverse-transform: X = -ln(1-U)/λ."""
    if lam <= 0:
        raise ValueError(f"Lambda must be positive, got {lam}")
    u = random.random()
    while u == 0.0:
        u = random.random()
    return -math.log(1.0 - u) / lam


def normal_variate(mu, sigma):
    """Generate Normal(mu, sigma) variate via Box-Muller transform."""
    if sigma < 0:
        raise ValueError(f"Sigma must be non-negative, got {sigma}")
    if sigma == 0:
        return mu
    u1 = random.random()
    u2 = random.random()
    while u1 == 0.0:
        u1 = random.random()
    z = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
    return mu + sigma * z


def poisson_variate(lam):
    """Generate Poisson(lambda) variate via Knuth's algorithm."""
    if lam < 0:
        raise ValueError(f"Lambda must be non-negative, got {lam}")
    if lam == 0:
        return 0
    # Normal approximation for large lambda (performance)
    if lam > 30:
        return max(0, round(normal_variate(lam, math.sqrt(lam))))
    L = math.exp(-lam)
    k = 0
    p = 1.0
    while True:
        k += 1
        p *= random.random()
        if p < L:
            break
    return k - 1


def compute_eoq(annual_demand, ordering_cost, holding_cost):
    """EOQ = sqrt((2 * D * S) / H). Returns 1.0 if inputs invalid."""
    if annual_demand <= 0 or ordering_cost <= 0 or holding_cost <= 0:
        return 1.0
    return math.sqrt((2.0 * annual_demand * ordering_cost) / holding_cost)


def compute_safety_stock(z_score, std_dev_demand, lead_time):
    """Safety Stock = Z * sigma_d * sqrt(LT)."""
    if lead_time <= 0 or std_dev_demand <= 0:
        return 0.0
    return z_score * std_dev_demand * math.sqrt(lead_time)


def compute_reorder_point(avg_daily_demand, lead_time, safety_stock):
    """ROP = (avg_daily_demand * lead_time) + safety_stock."""
    return (avg_daily_demand * lead_time) + safety_stock
