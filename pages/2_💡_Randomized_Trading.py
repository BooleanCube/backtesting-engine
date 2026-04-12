import os
import streamlit as st

st.set_page_config(page_title="Randomized Trading", page_icon="💡")

st.markdown("# Randomized Trading Strategy")
st.sidebar.header("Randomized Trading Strategy")
st.write(
    """
    This page demonstrates a simple randomized trading strategy implemented in the backtesting engine.
    The strategy randomly decides to go LONG, SHORT, or do nothing for each symbol at each time step.
    This is purely for testing the simulation logic and handler functioning of the backtesting engine.
    """
)

from simulate import run

# --- Run the backtest ---
strategy_id = 'RANDOM'
datapaths = [f[:-4] for f in os.listdir('./data/') if f.endswith('.csv')]
initial_capital = 100000.0

if st.button("Run Backtest"):
    with st.spinner("Running backtest..."):
        run(strategy_id, datapaths, initial_capital)

