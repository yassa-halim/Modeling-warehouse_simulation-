"""
analysis/abc.py — ABC Inventory Classification
================================================
Classifies products using Pareto analysis on outbound volume:
  A: cumulative 80%  of total outbound (typically ~20% of products)
  B: next 15%  (cumulative 95%)
  C: remaining 5%  (cumulative 100%)
"""


def classify_abc(products: list) -> list:
    """Add 'abc_class' key ('A'|'B'|'C') to each product dict (in-place)."""
    total = sum(p.get("total_outbound_qty", 0) for p in products)
    if total <= 0:
        for p in products:
            p["abc_class"] = "C"
        return products

    cumulative = 0.0
    for p in products:
        cumulative += p.get("total_outbound_qty", 0)
        pct = cumulative / total
        if pct <= 0.80:
            p["abc_class"] = "A"
        elif pct <= 0.95:
            p["abc_class"] = "B"
        else:
            p["abc_class"] = "C"

    return products


def get_abc_summary(products: list) -> dict:
    """Return count and volume % for each class."""
    total_vol = sum(p.get("total_outbound_qty", 0) for p in products)
    summary = {"A": {"count": 0, "volume": 0.0},
               "B": {"count": 0, "volume": 0.0},
               "C": {"count": 0, "volume": 0.0}}
    for p in products:
        cls = p.get("abc_class", "C")
        summary[cls]["count"]  += 1
        summary[cls]["volume"] += p.get("total_outbound_qty", 0)

    for cls in summary:
        vol = summary[cls]["volume"]
        summary[cls]["volume_pct"] = vol / total_vol * 100 if total_vol > 0 else 0.0

    return summary


def get_pareto_data(products: list) -> list:
    """Return list of dicts for Pareto chart."""
    total = sum(p.get("total_outbound_qty", 0) for p in products)
    if total <= 0:
        return []

    result = []
    cumulative = 0.0
    for p in products:
        cumulative += p.get("total_outbound_qty", 0)
        result.append({
            "name":           p.get("product_name", "")[:25],
            "outbound":       p.get("total_outbound_qty", 0),
            "cumulative_pct": round(cumulative / total * 100, 2),
            "abc_class":      p.get("abc_class", "C"),
        })
    return result
