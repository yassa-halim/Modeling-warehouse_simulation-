"""Tab 7 — 💾 Export: Download report & CSV, preview"""
import streamlit as st
from analysis.reports import generate_text_report, export_simulation_csv


def render(products, sim):
    st.markdown('<div class="sh">💾 Download Your Simulation Results</div>',
                unsafe_allow_html=True)
    st.caption("Download a full report or raw data to share with your team.")

    report_md = generate_text_report(products, sim_results=sim)
    sim_csv   = export_simulation_csv(sim)

    c1, c2 = st.columns(2)
    c1.download_button("📄 Download Full Report (.md)", data=report_md,
        file_name="warehouse_report.md", mime="text/markdown")
    c2.download_button("📊 Download Raw Data (.csv)", data=sim_csv,
        file_name="simulation_results.csv", mime="text/csv")

    st.markdown('<div class="sh">📋 Report Preview</div>', unsafe_allow_html=True)
    st.markdown(report_md)
