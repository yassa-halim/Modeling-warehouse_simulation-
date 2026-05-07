"""Dashboard tab modules."""
from dashboard.tabs import overview
from dashboard.tabs import flow_analysis
from dashboard.tabs import simulation_tab
from dashboard.tabs import warehouses
from dashboard.tabs import recommendations
from dashboard.tabs import charts
from dashboard.tabs import export

__all__ = [
    "overview", "flow_analysis", "simulation_tab",
    "warehouses", "recommendations", "charts", "export",
]
