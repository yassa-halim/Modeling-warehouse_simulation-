"""Tab 1 — 📊 Overview: KPIs, ABC Classification, Pareto Chart"""
import streamlit as st
import plotly.graph_objects as go
from analysis.abc import get_abc_summary, get_pareto_data


def render(products, wh_set):
    total_in  = sum(p["total_inbound_qty"]    for p in products)
    total_out = sum(p["total_outbound_qty"]   for p in products)
    total_adj = sum(p["total_adjustment_qty"] for p in products)
    abc_s     = get_abc_summary(products)

    # ── KPI Cards ────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    for col, (v, l) in zip([c1, c2, c3, c4, c5], [
        (f"{len(products):,}", "Products"),
        (f"{len(wh_set):,}", "Warehouses"),
        (f"{total_in:,.0f}", "Total Inbound"),
        (f"{total_out:,.0f}", "Total Outbound"),
        (f"{total_adj:,.0f}", "Adjustments"),
    ]):
        col.markdown(
            f'<div class="kcard"><div class="kval">{v}</div>'
            f'<div class="klbl">{l}</div></div>',
            unsafe_allow_html=True,
        )

    # ── ABC Classification ───────────────────────────────────────────────
    st.markdown('<div class="sh">🏷️ ABC Classification</div>', unsafe_allow_html=True)
    ca, cb, cc = st.columns(3)
    for col, (cls, color, bg) in zip([ca, cb, cc], [
        ("A", "#34d399", "#064e3b"),
        ("B", "#60a5fa", "#1e3a5f"),
        ("C", "#f472b6", "#3b1f2b"),
    ]):
        col.markdown(f"""
        <div style="background:{bg};border-radius:12px;padding:18px;text-align:center;">
          <div style="font-size:1.4rem;font-weight:800;color:{color}">Class {cls}</div>
          <div style="color:#e2e8f0;font-size:1.1rem">{abc_s[cls]['count']} products</div>
          <div style="color:{color}">{abc_s[cls]['volume_pct']:.1f}% of volume</div>
        </div>""", unsafe_allow_html=True)

    # ── Pareto Chart ─────────────────────────────────────────────────────
    st.markdown('<div class="sh">📈 Pareto — Cumulative Outbound Volume</div>',
                unsafe_allow_html=True)
    pareto = get_pareto_data(products)
    colors = {"A": "#34d399", "B": "#60a5fa", "C": "#f472b6"}
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[d["name"] for d in pareto[:50]],
        y=[d["outbound"] for d in pareto[:50]],
        marker_color=[colors[d["abc_class"]] for d in pareto[:50]],
        name="Outbound Qty",
    ))
    fig.add_trace(go.Scatter(
        x=[d["name"] for d in pareto[:50]],
        y=[d["cumulative_pct"] for d in pareto[:50]],
        mode="lines", name="Cumulative %",
        yaxis="y2", line=dict(color="#fbbf24", width=2.5),
    ))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", height=380, margin=dict(t=5, b=60),
        xaxis_tickangle=-40,
        yaxis=dict(title="Outbound Qty"),
        yaxis2=dict(title="Cumulative %", overlaying="y", side="right",
                    range=[0, 105], tickformat=".0f%%"),
        legend=dict(orientation="h", y=1.08),
        font=dict(family="Inter"),
    )
    st.plotly_chart(fig, use_container_width=True)
