"""analysis — ABC classification, reports, and recommendations."""
from analysis.abc import classify_abc, get_abc_summary, get_pareto_data
from analysis.reports import (
    compute_aggregate_kpis,
    generate_text_report,
    export_simulation_csv,
    get_reorder_recommendations,
)

__all__ = [
    "classify_abc", "get_abc_summary", "get_pareto_data",
    "compute_aggregate_kpis", "generate_text_report",
    "export_simulation_csv", "get_reorder_recommendations",
]
