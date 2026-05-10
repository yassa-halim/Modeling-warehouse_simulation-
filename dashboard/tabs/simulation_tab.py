"""Tab 3 — ⚙️ Simulation: Policy comparison, radar, per-product table"""
import streamlit as st
import plotly.graph_objects as go


def render(sim, kA, kB, kC):
    # ── Policy Cards ─────────────────────────────────────────────────────
    st.markdown('<div class="sh">Reorder Policy Comparison — FOQ vs EOQ vs JIT</div>',
                unsafe_allow_html=True)
    st.caption("**FOQ** = Fixed Order Quantity (always order 200 units) · "
               "**EOQ** = Economic Order Quantity (mathematically optimized) · "
               "**JIT** = Just-In-Time (minimal stock, order only when critical)")
    cols = st.columns(3)
    for col, (lbl, k, color) in zip(cols, [
        ("FOQ", kA, "#f472b6"), ("EOQ", kB, "#34d399"), ("JIT", kC, "#fbbf24")
    ]):
        col.markdown(f"""
        <div style="background:#1e293b;border-radius:12px;padding:16px;
             border:2px solid {color}33;">
           <div style="color:{color};font-weight:800;font-size:1.1rem">{lbl} Policy</div>
          <hr style="border-color:{color}33;margin:8px 0">
          <div style="color:#94a3b8;font-size:.75rem">Demand Coverage (Fill Rate)</div>
          <div style="color:#f1f5f9;font-size:1.2rem;font-weight:700">{k['fill_rate']:.1%}</div>
          <div style="color:#94a3b8;font-size:.75rem;margin-top:8px">Orders Fully Fulfilled</div>
          <div style="color:#f1f5f9;font-size:1.2rem;font-weight:700">{k['service_level']:.1%}</div>
          <div style="color:#94a3b8;font-size:.75rem;margin-top:8px">Out-of-Stock Rate</div>
          <div style="color:#f1f5f9;font-size:1.2rem;font-weight:700">{k['stockout_rate']:.1%}</div>
          <div style="color:#94a3b8;font-size:.75rem;margin-top:8px">Total Cost (Storage + Orders)</div>
          <div style="color:{color};font-size:1.3rem;font-weight:800">{k['total_cost']:,.0f}</div>
        </div>""", unsafe_allow_html=True)

    best = min([("FOQ", kA), ("EOQ", kB), ("JIT", kC)],
               key=lambda x: x[1]["total_cost"])
    st.success(f"✅ Best Policy: **{best[0]}** — "
               f"Achieves the lowest total cost at ${best[1]['total_cost']:,.0f}")

    # ── Radar Chart ──────────────────────────────────────────────────────
    st.markdown('<div class="sh">Policy Performance Radar</div>', unsafe_allow_html=True)
    cats = ["Demand Coverage", "Fulfillment Rate", "Stock Availability", "Cost Efficiency"]
    mc = max(kA["total_cost"], kB["total_cost"], kC["total_cost"], 1)
    fig = go.Figure()
    for nm, k, color, fill in [
        ("FOQ", kA, "#f472b6", "rgba(244,114,182,.12)"),
        ("EOQ", kB, "#34d399", "rgba(52,211,153,.12)"),
        ("JIT", kC, "#fbbf24", "rgba(251,191,36,.12)"),
    ]:
        v = [k["fill_rate"], k["service_level"],
             1 - k["stockout_rate"], 1 - k["total_cost"] / mc]
        fig.add_trace(go.Scatterpolar(
            r=v + [v[0]], theta=cats + [cats[0]],
            fill="toself", name=nm, fillcolor=fill,
            line=dict(color=color, width=2)))
    fig.update_layout(
        polar=dict(bgcolor="rgba(0,0,0,0)",
                   radialaxis=dict(visible=True, range=[0, 1])),
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        height=380, margin=dict(t=5), font=dict(family="Inter"))
    st.plotly_chart(fig, width="stretch")

    # ── Per-Product Table ────────────────────────────────────────────────
    st.markdown('<div class="sh">Detailed Results Per Product</div>', unsafe_allow_html=True)
    tbl = []
    for ra, rb, rc in zip(sim["policy_a"], sim["policy_b"], sim["policy_c"]):
        tbl.append({
            "Product Name":  ra["item_name"][:30],
            "FOQ Coverage": f"{ra['fill_rate']:.1%}",
            "EOQ Coverage": f"{rb['fill_rate']:.1%}",
            "JIT Coverage": f"{rc['fill_rate']:.1%}",
            "FOQ Cost $": f"{ra['total_cost']:,.0f}",
            "EOQ Cost $": f"{rb['total_cost']:,.0f}",
            "JIT Cost $": f"{rc['total_cost']:,.0f}",
            "Winner": min(
                [("FOQ", ra["total_cost"]), ("EOQ", rb["total_cost"]),
                 ("JIT", rc["total_cost"])],
                key=lambda x: x[1])[0],
        })
    st.dataframe(tbl, width="stretch", height=400)
