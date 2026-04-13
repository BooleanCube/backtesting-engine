import numpy as np
import pandas as pd

from utils.constants import INTERVALS, INTERVAL_PERIODS

def calculate_sharpe_ratio(returns, interval):
    """
    Calculates the annualized Sharpe ratio of a returns stream.
    
    Parameters:
    returns (pd.Series): A pandas Series representing period percentage returns.
    interval (str): Daily (252), Hourly (252*6.5), Minutely (252*6.5*60), etc.
    
    Returns:
    float: The annualized Sharpe Ratio.
    """
    periods = INTERVAL_PERIODS[INTERVALS.index(interval)]
    risk_free_rate = 0.03

    if len(returns) == 0 or np.std(returns) == 0: return 0.0
    return np.sqrt(periods) * ((np.mean(returns) - risk_free_rate) / np.std(returns))

def calculate_drawdowns(pnl_curve):
    """
    Calculates the largest peak-to-trough drawdown of the PnL curve
    as well as the duration of the drawdown.
    
    Parameters:
    pnl_curve (pd.Series): A pandas Series representing the cumulative equity curve.
    
    Returns:
    tuple: (drawdown_series, max_drawdown, max_duration)
    """
    # Calculate the running maximum (High Water Mark)
    hwm = pnl_curve.cummax()
    
    # Calculate the drawdown as a percentage from the High Water Mark
    drawdowns = (hwm - pnl_curve) / hwm
    max_drawdown = drawdowns.max()
    
    # Calculate drawdown durations
    durations = pd.Series(index=drawdowns.index, dtype=int)
    current_duration = 0
    
    for idx, value in drawdowns.items():
        if value == 0: current_duration = 0
        else: current_duration += 1
        durations[idx] = current_duration
        
    max_duration = durations.max()
    
    return drawdowns, max_drawdown, durations, max_duration


#  TODO: study and implement calmar ratio correctly, i think it might be calculating annual return wrong.
def calculate_calmar_ratio(pnl_curve, interval):
    """
    Calculates the Calmar ratio of a returns stream.
    
    Parameters:
    pnl_curve (pd.Series): A pandas Series representing the cumulative equity curve.
    interval (str): Daily (252), Hourly (252*6.5), Minutely (252*6.5*60), etc.
    
    Returns:
    float: The Calmar Ratio.
    """
    periods = INTERVAL_PERIODS[INTERVALS.index(interval)]
    annual_return = (pnl_curve.iloc[-1] / pnl_curve.iloc[0]) ** (periods / len(pnl_curve)) - 1
    _, max_drawdown, _, _ = calculate_drawdowns(pnl_curve)
    
    if max_drawdown == 0: return np.inf
    return annual_return / max_drawdown


def calculate_sortino_ratio(returns, interval):
    """
    Calculates the annualized Sortino ratio of a returns stream.
    
    Parameters:
    returns (pd.Series): A pandas Series representing period percentage returns.
    interval (str): Daily (252), Hourly (252*6.5), Minutely (252*6.5*60), etc.
    
    Returns:
    float: The annualized Sortino Ratio.
    """
    periods = INTERVAL_PERIODS[INTERVALS.index(interval)]
    risk_free_rate = 0.03
    minimum_acceptable_return = risk_free_rate # can change based on strategy or investor preference

    if len(returns) == 0: return 0.0
    downside_returns = returns[returns < minimum_acceptable_return]
    if len(downside_returns) == 0: return np.inf
    
    return np.sqrt(periods) * ((np.mean(returns) - risk_free_rate) / np.std(downside_returns))


def calculate_profit_factor(pointly_pnl):
    """
    Calculates the profit factor of a returns stream.
    
    Parameters:
    pointly_pnl (pd.Series): A pandas Series representing point-in-time profit and loss values.
    
    Returns:
    float: The Profit Factor.
    """
    total_gains = pointly_pnl[pointly_pnl > 0].sum()
    total_losses = -pointly_pnl[pointly_pnl < 0].sum()

    if total_losses == 0: return np.inf
    return total_gains / total_losses


def calculate_roi(initial_capital, final_capital):
    """
    Calculates the return on investment (ROI) percentage.
    
    Parameters:
    initial_capital (float): The initial amount of capital invested.
    final_capital (float): The final amount of capital after the investment period.
    
    Returns:
    float: The ROI percentage.
    """
    if initial_capital == 0: return 0.0
    return ((final_capital - initial_capital) / initial_capital) * 100