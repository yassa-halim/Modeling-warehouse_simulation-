"""Tab 5 — 📝 Recommendations: Reorder urgency + net inventory chart"""
import streamlit as st
import plotly.graph_objects as go
from analysis.reports import get_reorder_recommendations


def render(products, sim):
    st.markdown('<div class="sh">🚨 Products That Need Reordering (Sorted by Urgency)</div>', unsafe_allow_html=True)
    recs = get_reorder_recommendations(products, sim_results=sim, top_n=30)
    st.dataframe(recs, width="stretch", height=480)

    st.markdown('<div class="sh">Current Stock Levels — Surplus vs Deficit</div>', unsafe_allow_html=True)
    top25 = products[:25]
    nets  = [p["net_qty"] for p in top25]
    fig = go.Figure(go.Bar(
        x=[p["product_name"][:22] for p in top25], y=nets,
        marker_color=["#34d399" if n >= 0 else "#f87171" for n in nets],
    ))
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", height=340, margin=dict(t=5),
        xaxis_tickangle=-40, yaxis_title="Net Stock (units)")
    st.caption("🟢 Green = Stock surplus (safe) | 🔴 Red = Stock deficit (needs reorder)")
    st.plotly_chart(fig, width="stretch")
