"""Tab 4 — 🏭 Warehouses: Per-warehouse EOQ simulation results"""
import streamlit as st
import plotly.graph_objects as go


def render(wh_rows):
    st.markdown('<div class="sh">Per-Warehouse Simulation Results (EOQ Policy, Top 20 Products)</div>',
                unsafe_allow_html=True)
    if wh_rows:
        st.dataframe(wh_rows, width="stretch", height=420)

        wh_cost = {}
        for r in wh_rows:
            wh_cost[r["warehouse_id"]] = wh_cost.get(r["warehouse_id"], 0) + r["total_cost"]
        wh_cost = dict(sorted(wh_cost.items(), key=lambda x: x[1], reverse=True))
        fig = go.Figure(go.Bar(
            x=list(wh_cost.keys()), y=list(wh_cost.values()),
            marker_color="#818cf8"))
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)", height=320, margin=dict(t=5),
            xaxis_title="Warehouse ID", yaxis_title="Total Simulated Cost ($)")
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("No multi-warehouse data available.")
