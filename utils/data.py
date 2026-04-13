from datetime import datetime as dt
import pandas as pd
import os
import pytz

from utils.constants import DATA_DIR


def load_data_catalog():
    # Scans the data directory and extracts date ranges for each CSV.

    catalog = []
    if not os.path.exists(DATA_DIR): return pd.DataFrame()

    eastern = pytz.timezone('America/New_York')

    for file in os.listdir(DATA_DIR):
        if not file.endswith('.csv'): continue

        try:
            # Parse: AAPL_1m_202401010930_202401051600.csv
            parts = file.replace('.csv', '').split('_')
            
            # Enforce the strict 4-part naming convention
            if len(parts) == 4:
                symbol, interval, start_str, end_str = parts
                
                # Parse dates, localize to EST/EDT, then convert to UTC
                start_dt = eastern.localize(dt.strptime(start_str, '%Y%m%d%H%M')).astimezone(pytz.UTC)
                end_dt = eastern.localize(dt.strptime(end_str, '%Y%m%d%H%M')).astimezone(pytz.UTC)

                catalog.append({
                    'Filename': file,
                    'Symbol': symbol,
                    'Interval': interval,
                    'Start': start_dt,
                    'End': end_dt,
                    'Path': os.path.join(DATA_DIR, file)
                })
        except Exception as e:
            print(f"Error processing {file}: {e}")

    return pd.DataFrame(catalog)


def check_overlapping_intervals(selected_df):
    # Checks for overlapping time intervals within the same symbol.

    conflicts = []
    for symbol, group in selected_df.groupby('Symbol'):
        if len(group) > 1:
            sorted_group = group.sort_values('Start')
            for i in range(1, len(sorted_group)):
                prev_end = sorted_group.iloc[i-1]['End']
                curr_start = sorted_group.iloc[i]['Start']
                if curr_start <= prev_end:
                    conflicts.append(symbol)
                    break # One conflict is enough to flag this specific symbol
                    
    return conflicts


def check_unique_periods(selected_df):
    # Checks if all selected files share the same interval period (e.g., 1m, 5m, 1h).

    return selected_df['Interval'].unique().tolist()