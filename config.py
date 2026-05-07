"""config.py — Central Configuration"""

# ── App ───────────────────────────────────────
APP_TITLE     = "Warehouse Inventory Flow Simulation"
CSV_FILE_PATH = "warehouse-inventory-flow-dataset.csv"

# ── Simulation ────────────────────────────────
SIMULATION_HORIZON_DAYS  = 90
INITIAL_STOCK_MULTIPLIER = 15

# ── Policies ──────────────────────────────────
FOQ_ORDER_SIZE         = 200
FOQ_REORDER_POINT_DAYS = 7
JIT_SAFETY_DAYS        = 2    # JIT: reorder only when stock < 2 days demand

# ── Lead Time ─────────────────────────────────
LEAD_TIME_MEAN = 3.0
LEAD_TIME_STD  = 0.8
MIN_LEAD_TIME  = 1.0

# ── Costs ─────────────────────────────────────
DEFAULT_HOLDING_COST  = 5.0
DEFAULT_ORDERING_COST = 50.0
SERVICE_LEVEL_Z       = 1.65
