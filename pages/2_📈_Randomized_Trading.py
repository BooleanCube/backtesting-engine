import os
import pandas as pd
import streamlit as st
import plotly.express as px
from simulate import run

from utils.data import load_data_catalog, check_overlapping_intervals, check_unique_periods

# --- Page Config ---
st.set_page_config(page_title="Randomized Trading", page_icon="📈", layout="wide")

# --- UI Setup ---
st.markdown("# Randomized Trading Strategy")
st.sidebar.header("Strategy Configuration")

st.write(
    """
    This page demonstrates a simple randomized trading strategy implemented in the backtesting engine.
    The strategy randomly decides to go LONG, SHORT, or do nothing for each symbol at each time step.
    This is purely for testing the simulation logic and handler functioning of the backtesting engine.
    """
)

# 1. Load Data Catalog
catalog_df = load_data_catalog()

if catalog_df.empty:
    st.error("No valid CSV data found in `./data/`. Please ensure the directory exists and contains CSV files with a recognizable Date/Time column.")
    st.stop()

# 2. Select Data
st.subheader("1. Data Selection")
selected_files = st.multiselect(
    "Select historical data files to include in the simulation:",
    options=catalog_df['Filename'].tolist(),
    default=[]
)

# Filter the catalog based on user selection
selected_data = catalog_df[catalog_df['Filename'].isin(selected_files)].copy()

if not selected_data.empty:
    selected_data['Start'] = pd.to_datetime(selected_data['Start'], utc=True)
    selected_data['End'] = pd.to_datetime(selected_data['End'], utc=True)

# 3. Conflict Check
overlapping_conflicts = check_overlapping_intervals(selected_data) if not selected_data.empty else []
unique_periods = check_unique_periods(selected_data) if not selected_data.empty else []
period_mismatch = len(unique_periods) > 1
can_run = False

if overlapping_conflicts:
    st.error(f"⚠️ **Time Range Conflict Detected!** Overlapping histories found for: **{', '.join(overlapping_conflicts)}**. Please deselect conflicting files.")
elif period_mismatch:
    st.error(f"⚠️ **Interval Mismatch Detected!** You selected files with different timeframes (**{', '.join(unique_periods)}**). All histories must share the same interval period.")
elif not selected_data.empty:
    st.success("✅ No time conflicts detected. Data is ready for simulation.")
    can_run = True
else:
    st.info("Please select at least one dataset to proceed.")

# 4. Plot Time Intervals
st.subheader("2. Data Timeline Visualization")
if not selected_data.empty:
    selected_data['Start'] = pd.to_datetime(selected_data['Start'], utc=True)
    selected_data['End'] = pd.to_datetime(selected_data['End'], utc=True)

    # Use Plotly Express timeline (Gantt chart) to visualize working data ranges
    fig = px.timeline(
        selected_data,
        x_start="Start",
        x_end="End",
        y="Symbol",
        color="Filename",
        title="Selected Historical Data Intervals",
        labels={"Symbol": "Ticker Symbol"}
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(showlegend=True, height=200 + (len(selected_data) * 75))
    st.plotly_chart(fig, width='stretch')

# 5. Customizable Capital
st.subheader("3. Simulation Parameters")
initial_capital = st.number_input(
    "Initial Capital ($)",
    min_value=1000.0,
    value=100000.0,
    step=5000.0,
    format="%.2f"
)

# --- Execution ---
st.divider()

if st.button("Run Backtest", disabled=not can_run, type="primary"):
    # Strip '.csv' from selected files to match your engine's expected input
    datapaths = [f[:-4] for f in selected_files]

    with st.spinner("Running backtest..."):
        res = run('RANDOM', datapaths, initial_capital)
        print(res)
        st.success("Simulation completed successfully! (Results display pending)")