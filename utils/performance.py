import numpy as np
import pandas as pd

from utils.constants import INTERVALS, INTERVAL_PERIODS


RISK_FREE_RATE = 0.00

def calculate_sharpe_ratio(returns, interval):
    periods = INTERVAL_PERIODS[INTERVALS.index(interval)]

    if len(returns) == 0 or np.std(returns) == 0: return 0.0
    return np.sqrt(periods) * ((np.mean(returns) - RISK_FREE_RATE) / np.std(returns))


def calculate_drawdowns(equity_curve):
    hwm = equity_curve.cummax() # high water mark
    drawdowns = (hwm - equity_curve) / hwm
    max_drawdown = drawdowns.max()
    
    return drawdowns, max_drawdown


def calculate_calmar_ratio(equity_curve, interval):
    periods = INTERVAL_PERIODS[INTERVALS.index(interval)]
    cagr = (equity_curve.iloc[-1] / equity_curve.iloc[0]) ** (periods / len(equity_curve)) - 1 # compound annual growth rate
    _, max_drawdown = calculate_drawdowns(equity_curve)
    
    if max_drawdown == 0: return np.inf
    return cagr / max_drawdown


def calculate_sortino_ratio(returns, interval):
    periods = INTERVAL_PERIODS[INTERVALS.index(interval)]
    minimum_acceptable_return = RISK_FREE_RATE # can change based on strategy or investor preference

    if len(returns) == 0: return 0.0
    downside_returns = returns[returns < minimum_acceptable_return]
    if len(downside_returns) == 0: return np.inf
    
    return np.sqrt(periods) * ((np.mean(returns) - RISK_FREE_RATE) / np.std(downside_returns))


def calculate_profit_factor(periodic_pnl):
    total_gains = (periodic_pnl[periodic_pnl > 0]).sum()
    total_losses = (-periodic_pnl[periodic_pnl < 0]).sum()

    if total_losses == 0: return np.inf
    return total_gains / total_losses


def calculate_roi(initial_capital, final_capital):
    if initial_capital == 0: return 0.0
    return ((final_capital - initial_capital) / initial_capital) * 100