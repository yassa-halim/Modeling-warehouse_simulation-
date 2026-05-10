"""Tab 2 — 🔄 Flow Analysis: Movement breakdown, scatter, state chart, table"""
import streamlit as st
import plotly.graph_objects as go


def render(products):
    total_in  = sum(p["total_inbound_qty"]    for p in products)
    total_out = sum(p["total_outbound_qty"]   for p in products)
    total_tr  = sum(p["total_transfer_qty"]   for p in products)
    total_adj = sum(p["total_adjustment_qty"] for p in products)

    c1, c2 = st.columns(2)

    # ── Movement Type Donut ──────────────────────────────────────────────
    with c1:
        st.markdown('<div class="sh">Inventory Movement Breakdown</div>', unsafe_allow_html=True)
        fig = go.Figure(go.Pie(
            labels=["Inbound", "Outbound", "Transfer", "Adjustment"],
            values=[total_in, total_out, total_tr, total_adj],
            marker=dict(colors=["#34d399", "#f472b6", "#818cf8", "#fbbf24"]),
            hole=0.45,
        ))
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                          height=320, margin=dict(t=5), font=dict(family="Inter"))
        st.plotly_chart(fig, width="stretch")

    # ── Inbound vs Outbound Scatter ──────────────────────────────────────
    with c2:
        st.markdown('<div class="sh">Received vs Shipped — Top 30 Products</div>', unsafe_allow_html=True)
        fig = go.Figure(go.Scatter(
            x=[p["total_inbound_qty"] for p in products[:30]],
            y=[p["total_outbound_qty"] for p in products[:30]],
            mode="markers", text=[p["product_name"][:20] for p in products[:30]],
            marker=dict(size=9, color="#6366f1",
                        line=dict(color="#a5b4fc", width=1)),
        ))
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)", height=320, margin=dict(t=5),
            xaxis_title="Units Received (Inbound)", yaxis_title="Units Shipped (Outbound)",
            font=dict(family="Inter"))
        st.plotly_chart(fig, width="stretch")

    # ── State-Level Activity ─────────────────────────────────────────────
    st.markdown('<div class="sh">Outbound Activity by State / Region</div>', unsafe_allow_html=True)
    sv = {}
    for p in products:
        s = p.get("primary_warehouse_state", "")
        if s:
            sv[s] = sv.get(s, 0) + p["total_outbound_qty"]
    sv = dict(sorted(sv.items(), key=lambda x: x[1], reverse=True))
    fig = go.Figure(go.Bar(x=list(sv.keys()), y=list(sv.values()),
        marker_color="#6366f1"))
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", height=300, margin=dict(t=5),
        xaxis_title="State / Region", yaxis_title="Total Units Shipped")
    st.plotly_chart(fig, width="stretch")

    # ── Full Flow Table ──────────────────────────────────────────────────
    st.markdown('<div class="sh">Complete Product Flow Details</div>', unsafe_allow_html=True)
    st.dataframe([{
        "Product Name": p["product_name"][:30], "SKU": p["sku"],
        "Warehouse": p["primary_warehouse_name"][:22],
        "City": p["primary_warehouse_city"],
        "UOM": p["unit_of_measure"],
        "Received": round(p["total_inbound_qty"], 0),
        "Shipped": round(p["total_outbound_qty"], 0),
        "Transferred": round(p["total_transfer_qty"], 0),
        "Adjusted": round(p["total_adjustment_qty"], 0),
        "Net Stock": round(p["net_qty"], 0),
        "Active Days": p["active_days"],
        "ABC": p.get("abc_class", "?"),
        "First Move": p["first_movement_dt"],
        "Last Move": p["last_movement_dt"],
    } for p in products], width="stretch", height=420)
