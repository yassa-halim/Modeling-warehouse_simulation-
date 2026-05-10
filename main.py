"""
main.py — Warehouse Inventory Flow Simulation
==============================================
Usage:  streamlit run main.py
"""
import os
import sys
import traceback

import streamlit as st

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from config import CSV_FILE_PATH
from data.loader import load_and_aggregate_from_csv
from simulation.engine import run_simulation_for_products
from simulation.warehouse import run_per_warehouse
from analysis.abc import classify_abc
from analysis.reports import compute_aggregate_kpis
from dashboard.styles import CSS
from dashboard.tabs import (
    overview, flow_analysis, simulation_tab,
    warehouses, recommendations, charts, export,
)

# ── Page Config ───────────────────────────────────────────────────────────
st.set_page_config(page_title="Warehouse Flow Simulation", page_icon="📦", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

CSV_PATH = os.path.join(ROOT, CSV_FILE_PATH)

# ── Sidebar Controls ─────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Simulation Settings")
    n_products    = st.slider("Number of products to simulate", 10, 100, 50, 5,
                              help="How many top products to include in the simulation")
    horizon       = st.slider("Simulation period (days)", 30, 180, 90, 10,
                              help="How many days to run the simulation for")
    holding_cost  = st.slider("Storage cost per unit per year ($)", 1.0, 20.0, 5.0, 0.5,
                              help="Annual cost of keeping one unit in the warehouse")
    ordering_cost = st.slider("Cost per purchase order ($)", 10.0, 200.0, 50.0, 5.0,
                              help="Fixed cost incurred each time a new order is placed")
    st.markdown("---")
    st.caption("🔄 Adjust any slider above to re-run the simulation")

# ── Data Loading (cached) ────────────────────────────────────────────────
@st.cache_data(show_spinner="⏳ Loading CSV...")
def _load(path):
    return classify_abc(load_and_aggregate_from_csv(path))

if not os.path.exists(CSV_PATH):
    st.error(f"❌ CSV not found: `{CSV_PATH}`")
    st.stop()

try:
    products = _load(CSV_PATH)
except Exception as e:
    st.error(f"❌ Error loading CSV: {e}")
    st.stop()

top = products[:n_products]

# ── Simulation (session_state cache) ─────────────────────────────────────
sim_key = f"{n_products}_{horizon}_{holding_cost}_{ordering_cost}"

if "sim_key" not in st.session_state or st.session_state.sim_key != sim_key:
    try:
        with st.spinner("⚙️ Running simulation..."):
            st.session_state.sim = run_simulation_for_products(
                top, max_products=n_products,
                horizon=horizon, holding_cost=holding_cost,
                ordering_cost=ordering_cost,
            )
        with st.spinner("🏭 Running warehouse sim..."):
            st.session_state.wh_rows = run_per_warehouse(
                top[:20], max_products=20,
                horizon=horizon, holding_cost=holding_cost,
                ordering_cost=ordering_cost,
            )
        st.session_state.sim_key = sim_key
    except Exception as e:
        st.error(f"❌ Simulation error: {e}")
        st.code(traceback.format_exc())
        st.stop()

sim     = st.session_state.sim
wh_rows = st.session_state.wh_rows

kA = compute_aggregate_kpis(sim["policy_a"])
kB = compute_aggregate_kpis(sim["policy_b"])
kC = compute_aggregate_kpis(sim["policy_c"])
wh_set = set(w for p in products for w in p.get("warehouses_used", []))

# ── Banner ────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:linear-gradient(135deg,#1e1b4b,#312e81,#1e293b);border-radius:16px;
 padding:28px 36px;margin-bottom:20px;border:1px solid rgba(129,140,248,.2);">
 <div style="font-size:1.8rem;font-weight:800;background:linear-gradient(135deg,#c7d2fe,#818cf8);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
  📦 Warehouse Inventory Flow &amp; Simulation Dashboard
 </div>
 <div style="color:#a5b4fc;margin-top:6px;">
  Analyzing <b style="color:#818cf8">{len(products):,} products</b> across
  <b style="color:#34d399">{len(wh_set):,} warehouses</b> ·
  Comparing 3 reorder policies (FOQ · EOQ · JIT) over a <b style="color:#fbbf24">{horizon}-day</b> period
 </div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────
tabs = st.tabs([
    "📊 Overview",
    "🔄 Inventory Flow",
    "⚙️ Policy Comparison",
    "🏭 Warehouse Performance",
    "📝 Reorder Alerts",
    "📈 Visual Charts",
    "💾 Download Reports",
])

with tabs[0]:
    overview.render(products, wh_set)
with tabs[1]:
    flow_analysis.render(products)
with tabs[2]:
    simulation_tab.render(sim, kA, kB, kC)
with tabs[3]:
    warehouses.render(wh_rows)
with tabs[4]:
    recommendations.render(products, sim)
with tabs[5]:
    charts.render(sim, kA, kB, kC)
with tabs[6]:
    export.render(products, sim)
