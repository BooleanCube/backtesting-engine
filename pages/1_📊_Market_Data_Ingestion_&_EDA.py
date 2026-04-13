import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import os
from datetime import datetime, time
import pytz

from utils import INTERVALS, INTRADAY_INTERVALS, INTERDAY_INTERVALS, DATA_DIR

# --- App Configuration ---
st.set_page_config(page_title="Market Data Ingestion & EDA", layout="wide")
st.title("📈 Market Data Ingestion & EDA")

# Initialize session state to prevent the page from clearing when sliders are used
if 'data_fetched' not in st.session_state:
    st.session_state['data_fetched'] = False

# --- Sidebar Controls ---
st.sidebar.header("Data Parameters")
ticker = st.sidebar.text_input("Symbol (e.g., AAPL, SPY)", value="AAPL").upper()

col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input("Start Date", value=pd.to_datetime("2020-01-01"), key="start_date")
    start_time = st.time_input("Start Time", value=datetime.strptime("09:30", "%H:%M").time(), key="start_time")
with col2:
    end_date = st.date_input("End Date", value=datetime.today(), key="end_date")
    end_time = st.time_input("End Time", value=datetime.strptime("16:00", "%H:%M").time(), key="end_time")

interval = st.sidebar.selectbox(
    "Interval",
    options=INTERVALS,
    index=7,
)

save_dir = DATA_DIR

# --- Fetch Data Function ---
@st.cache_data(ttl=3600)
def fetch_data(symbol, start, end, tf):
    df = yf.download(symbol, start=start, end=end, interval=tf)

    if df is None: return None
    if df.empty: return None

    # Flatten MultiIndex columns if yfinance returns them
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]

    expected_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    if not all(col in df.columns for col in expected_cols):
        st.error("Fetched data is missing required columns.")
        return None

    df = df[expected_cols]
    df.index.name = 'Date'
    
    if tf in INTERDAY_INTERVALS:
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
    else:
        if df.index.tz is None: 
            df.index = df.index.tz_localize('UTC').tz_convert('America/New_York')
        else: 
            df.index = df.index.tz_convert('America/New_York')

    # Base EDA Calculations
    df['Returns'] = df['Close'].pct_change()
    df['Log_Returns'] = np.log(df['Close'] / df['Close'].shift(1))
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['Vol_20d'] = df['Returns'].rolling(window=20).std() * (252 ** 0.5)
    
    # Advanced Quant Calculations
    df['Cum_Returns'] = (1 + df['Returns'].fillna(0)).cumprod() - 1
    rolling_max = df['Close'].cummax()
    df['Drawdown'] = (df['Close'] - rolling_max) / rolling_max
    
    # Outlier Calculation (Z-Score of Returns)
    returns_mean = df['Returns'].mean()
    returns_std = df['Returns'].std()
    df['Z_Score'] = (df['Returns'] - returns_mean) / returns_std

    return df

# --- Main Logic ---
if st.sidebar.button("Fetch & Analyze Data"):
    st.session_state['data_fetched'] = True

# Wrapping execution in session_state so sliders don't clear the screen
if st.session_state['data_fetched']:
    eastern = pytz.timezone('America/New_York')
    start_dt_est = eastern.localize(datetime.combine(start_date, start_time))
    end_dt_est = eastern.localize(datetime.combine(end_date, end_time))

    interval_offsets = {"1m": pd.Timedelta(minutes=1), "2m": pd.Timedelta(minutes=2), "5m": pd.Timedelta(minutes=5), "15m": pd.Timedelta(minutes=15), "30m": pd.Timedelta(minutes=30), "1h": pd.Timedelta(hours=1), "4h": pd.Timedelta(hours=4)}
    if interval in interval_offsets: yf_start_dt_est = start_dt_est - interval_offsets[interval]
    else: yf_start_dt_est = start_dt_est
        
    start_dt_utc = yf_start_dt_est.astimezone(pytz.UTC)
    end_dt_utc = end_dt_est.astimezone(pytz.UTC)

    market_open = time(9, 30)
    market_close = time(16, 0)
    if interval in INTRADAY_INTERVALS and ((start_time < market_open) or (end_time > market_close)):
        st.warning("You selected a time outside regular NASDAQ trading hours (09:30–16:00 EST). Data may be missing or unavailable.")

    with st.spinner(f"Fetching data for {ticker}..."):
        # For daily data, we just pass the naive dates to yfinance
        if interval in INTERDAY_INTERVALS:
            df = fetch_data(ticker, start_date, end_date + pd.Timedelta(days=1), interval)
        else:
            df = fetch_data(ticker, start_dt_utc, end_dt_utc, interval)

    if df is not None:
        if interval in INTERDAY_INTERVALS:
            mask = (df.index >= pd.to_datetime(start_date)) & (df.index <= pd.to_datetime(end_date))
        else:
            mask = (df.index >= start_dt_est) & (df.index <= end_dt_est)
            
        df = df.loc[mask]
        st.success(f"Successfully fetched {len(df)} rows for {ticker}.")

        # --- Save Functionality ---
        # Extract the exact start and end timestamps from the fetched data index
        actual_start = df.index[0].strftime('%Y%m%d%H%M')
        actual_end = df.index[-1].strftime('%Y%m%d%H%M')
        
        # Standardized naming convention: Ticker_Interval_Start_End.csv
        filename = f"{ticker}_{interval}_{actual_start}_{actual_end}.csv"
            
        filepath = os.path.join(save_dir, filename)

        if st.button(f"💾 Save to {filepath}"):
            os.makedirs(save_dir, exist_ok=True)
            save_df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
            save_df.to_csv(filepath)
            st.success(f"Data saved successfully to `{filepath}`! Ready for CSVHandler ingestion.")

        # --- EDA Tabs ---
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🕯️ Price & Vol", 
            "📊 Distributions & Metrics", 
            "⚠️ Outliers", 
            "🕵️ Quality & Gaps",
            "🗄️ Raw Data"
        ])

        with tab1:
            st.subheader(f"{ticker} Price Action & Moving Averages")
            fig_price = go.Figure()
            fig_price.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'))
            fig_price.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], line=dict(color='#90D5FF', width=1), name='SMA 20'))
            fig_price.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], line=dict(color='#FFA500', width=1), name='SMA 50'))
            fig_price.update_layout(height=500, xaxis_rangeslider_visible=False, template="plotly_dark")
            st.plotly_chart(fig_price, width='stretch')

            fig_vol = go.Figure()
            fig_vol.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color='lightblue'))
            fig_vol.update_layout(height=250, template="plotly_dark", margin=dict(t=10, b=10))
            st.plotly_chart(fig_vol, width='stretch')

        with tab2:
            st.subheader("Statistical Distributions")
            col1, col2 = st.columns(2)
            with col1:
                fig_ret = px.histogram(df, x='Returns', nbins=100, marginal="box", template="plotly_dark", title="Daily Returns")
                st.plotly_chart(fig_ret, width='stretch')
            with col2:
                fig_volat = px.line(df, x=df.index, y='Vol_20d', template="plotly_dark", title="Rolling Volatility (20-Period)")
                st.plotly_chart(fig_volat, width='stretch')

            st.markdown("---")
            st.subheader("Advanced Quant Metrics")
            col3, col4 = st.columns(2)
            with col3:
                fig_cum = px.line(df, x=df.index, y='Cum_Returns', template="plotly_dark", title="Cumulative Returns")
                fig_cum.update_layout(yaxis_tickformat='.2%')
                st.plotly_chart(fig_cum, width='stretch')
            with col4:
                fig_dd = px.area(df, x=df.index, y='Drawdown', template="plotly_dark", title="Historical Drawdown")
                fig_dd.update_traces(fillcolor='rgba(255, 0, 0, 0.3)', line=dict(color='red'))
                fig_dd.update_layout(yaxis_tickformat='.2%')
                st.plotly_chart(fig_dd, width='stretch')

        with tab3:
            st.subheader("Outliers & Anomalies")
            outlier_threshold = st.slider("Z-Score Threshold", min_value=1.0, max_value=5.0, value=3.0, step=0.5)
            
            outliers = df[df['Z_Score'].abs() > outlier_threshold]
            
            fig_outliers = go.Figure()
            fig_outliers.add_trace(go.Scatter(x=df.index, y=df['Returns'], mode='markers', name='Normal Returns', marker=dict(color='gray', opacity=0.5)))
            fig_outliers.add_trace(go.Scatter(x=outliers.index, y=outliers['Returns'], mode='markers', name='Outliers', marker=dict(color='red', size=8)))
            fig_outliers.update_layout(height=400, template="plotly_dark", title=f"Returns Outliers (Threshold: ±{outlier_threshold}σ)")
            st.plotly_chart(fig_outliers, width='stretch')
            
            st.write(f"Detected **{len(outliers)}** outliers out of {len(df)} total periods.")
            st.dataframe(outliers[['Close', 'Returns', 'Volume', 'Z_Score']], width='stretch')

        with tab4:
            st.subheader("Data Quality & Gap Analysis")
            
            nan_counts = df[['Open', 'High', 'Low', 'Close', 'Volume']].isna().sum()
            total_nans = nan_counts.sum()
            
            col1, col2 = st.columns(2)
            with col1:
                if total_nans == 0:
                    st.success("✅ No NaN values found in the price/volume data.")
                else:
                    st.error(f"❌ Found missing values (NaNs).")
                    st.write(nan_counts[nan_counts > 0])

            with col2:
                time_diffs = df.index.to_series().diff()
                expected_interval = time_diffs.mode()[0]
                gap_mask = time_diffs > expected_interval
                
                if not gap_mask.any():
                    st.success(f"✅ No missing bars detected. Index is perfectly continuous at {expected_interval}.")
                else:
                    st.warning(f"⚠️ Detected {gap_mask.sum()} potential gaps in the time series.")
                    
                    raw_gaps = time_diffs[gap_mask]
                    missing_periods = (raw_gaps / expected_interval) - 1
                    
                    gap_df = pd.DataFrame({
                        'Missing Periods': missing_periods.apply(lambda x: f"{int(round(x))} missing bar(s)"),
                        'Previous Timestamp': raw_gaps.index - raw_gaps
                    })
                    st.dataframe(gap_df, width='stretch')

        with tab5:
            st.subheader("Formatted Dataset (Ready for CSVHandler)")
            st.dataframe(df[['Open', 'High', 'Low', 'Close', 'Volume']], width='stretch')

    else:
        st.warning("No data found. Check the ticker symbol and date range.")

