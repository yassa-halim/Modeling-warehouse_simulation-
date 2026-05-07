"""Tab 6 — 📈 Charts: Fill rate bars, cost breakdown, inventory timeline"""
import streamlit as st
import plotly.graph_objects as go


def render(sim, kA, kB, kC):
    # ── Fill Rate Bars ───────────────────────────────────────────────────
    st.markdown('<div class="sh">Fill Rate — FOQ vs EOQ vs JIT</div>',
                unsafe_allow_html=True)
    n20 = [r["item_name"][:18] for r in sim["policy_a"][:20]]
    fig = go.Figure()
    for lbl, pol, color in [
        ("FOQ", "policy_a", "#f472b6"),
        ("EOQ", "policy_b", "#34d399"),
        ("JIT", "policy_c", "#fbbf24"),
    ]:
        fig.add_trace(go.Bar(
            name=lbl, x=n20,
            y=[r["fill_rate"] for r in sim[pol][:20]],
            marker_color=color))
    fig.update_layout(barmode="group", template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=360, xaxis_tickangle=-40, margin=dict(t=5))
    st.plotly_chart(fig, use_container_width=True)

    # ── Cost Breakdown ───────────────────────────────────────────────────
    st.markdown('<div class="sh">Cost Breakdown</div>', unsafe_allow_html=True)
    fig = go.Figure()
    for lbl, k, color in [
        ("FOQ", kA, "#f472b6"), ("EOQ", kB, "#34d399"), ("JIT", kC, "#fbbf24")
    ]:
        fig.add_trace(go.Bar(
            name=f"{lbl} Holding", x=[lbl],
            y=[k["total_holding_cost"]], marker_color=color, opacity=0.9))
        fig.add_trace(go.Bar(
            name=f"{lbl} Ordering", x=[lbl],
            y=[k["total_ordering_cost"]], marker_color=color, opacity=0.45))
    fig.update_layout(barmode="stack", template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=360, margin=dict(t=5), yaxis_title="Cost ($)")
    st.plotly_chart(fig, use_container_width=True)

    # ── Inventory Over Time ──────────────────────────────────────────────
    st.markdown('<div class="sh">Inventory Level Over Time (Top Product)</div>',
                unsafe_allow_html=True)
    sa, sb, sc = sim["policy_a"][0], sim["policy_b"][0], sim["policy_c"][0]
    fig = go.Figure()
    for lbl, res, color, fill in [
        ("FOQ", sa, "#f472b6", "rgba(244,114,182,.07)"),
        ("EOQ", sb, "#34d399", "rgba(52,211,153,.07)"),
        ("JIT", sc, "#fbbf24", "rgba(251,191,36,.07)"),
    ]:
        snaps = res.get("inventory_snapshots", [])
        if snaps:
            fig.add_trace(go.Scatter(
                x=[s["day"] for s in snaps],
                y=[s["inventory"] for s in snaps],
                mode="lines", name=lbl,
                line=dict(color=color, width=2),
                fill="tozeroy", fillcolor=fill,
            ))
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", height=360, margin=dict(t=5),
        xaxis_title="Day", yaxis_title="Inventory (units)")
    st.caption(f"Product: **{sa['item_name']}**")
    st.plotly_chart(fig, use_container_width=True)
