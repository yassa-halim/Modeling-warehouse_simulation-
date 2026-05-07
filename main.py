"""
main.py — Warehouse Inventory Flow Simulation
==============================================
Usage:  streamlit run main.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dashboard.app import *  # noqa: F401, F403
