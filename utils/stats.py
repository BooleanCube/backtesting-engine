import pandas as pd
import numpy as np
import statsmodels.tsa.stattools as ts

def test_cointegration(series_x, series_y):
    """
    Performs the Augmented Dickey-Fuller (ADF) test to check for 
    cointegration between two time series.
    
    Parameters:
    series_x (pd.Series/np.array): Price series of asset A.
    series_y (pd.Series/np.array): Price series of asset B.
    
    Returns:
    float: The p-value of the cointegration test. A value < 0.05 
           typically rejects the null hypothesis, suggesting the 
           two series are cointegrated.
    """
    # ts.coint returns: t-statistic, p-value, and critical values
    coint_res = ts.coint(series_x, series_y)
    p_value = coint_res[1]
    
    return p_value

def calculate_rolling_z_score(spread_series, window):
    """
    Calculates the rolling Z-score of a spread time series.
    This is a vectorized equivalent of the logic used in the 
    MeanReversionPairs strategy.
    
    Parameters:
    spread_series (pd.Series): The price spread between two assets.
    window (int): The lookback window for the moving average and std dev.
    
    Returns:
    pd.Series: A rolling Z-score.
    """
    if not isinstance(spread_series, pd.Series):
        spread_series = pd.Series(spread_series)
        
    rolling_mean = spread_series.rolling(window=window).mean()
    rolling_std = spread_series.rolling(window=window).std()
    
    z_score = (spread_series - rolling_mean) / rolling_std
    
    return z_score