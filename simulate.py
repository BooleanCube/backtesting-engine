from queue import Queue
import time
import numpy as np

from engine.events import Event, MarketEvent, SignalEvent, OrderEvent, FillEvent
from engine.data import CSVHandler, DataHandler
from engine.execution import ExecutionHandler, SimulatedExecution
from engine.portfolio import Portfolio
from strategies.base import Strategy
from strategies.randomized import Randomized
from utils.performance import calculate_calmar_ratio, calculate_drawdowns, calculate_profit_factor, \
    calculate_roi, calculate_sharpe_ratio, calculate_sortino_ratio, calculate_cagr, calculate_volatility


def get_strategy(strategy_id, data_handler, events_queue):
    match strategy_id:
        case 'MRP':
            # change to mean reversion pair
            return Randomized(data_handler=data_handler, events_queue=events_queue)
        case _:
            return Randomized(data_handler=data_handler, events_queue=events_queue)

def run(strategy_id, selected_data, initial_capital):
    event_loop: Queue[Event] = Queue()
    data: DataHandler = CSVHandler(events_queue=event_loop, selected_histories=selected_data)
    portfolio: Portfolio = Portfolio(data_handler=data, events_queue=event_loop, initial_capital=initial_capital)
    strategy: Strategy = get_strategy(strategy_id=strategy_id, data_handler=data, events_queue=event_loop)
    broker: ExecutionHandler = SimulatedExecution(data_handler=data, events_queue=event_loop)

    print("Go For Broke: Starting the backtest event loop...\n")

    start_time = time.time()

    while 1:
        data.update_bars()
        if data.terminate_simulation: break

        while not event_loop.empty():
            event: Event = event_loop.get(False)

            match event:
                case MarketEvent():
                    portfolio.update_timeindex(event)
                    strategy.calculate_signals(event)
                case SignalEvent():
                    portfolio.generate_signal_order(event)
                case OrderEvent():
                    broker.execute_order(event)
                case FillEvent():
                    portfolio.fill_order(event)

    end_time = time.time()
    print(f"Backtest completed in {round(end_time - start_time, 2)} seconds.")

    results = portfolio.get_results_dataframe()

    final_capital = results['capital'].iloc[-1]
    pct_returns = results['capital'].pct_change()
    log_returns = np.log(results['capital']).diff()
    equity_curve = (1.0 + pct_returns).cumprod()
    total_upnl = results['capital'] - results['capital'].iloc[0] # unrealised pnl
    periodic_upnl = total_upnl.diff().fillna(0) # unrealised pnl per period
    total_rpnl = results['cash'] - results['cash'].iloc[0] # realised pnl
    periodic_rpnl = total_rpnl.diff().fillna(0) # realised pnl per period
    win_rate = portfolio.winning_trades / portfolio.closed_trades if portfolio.closed_trades > 0 else 0.0

    drawdowns, max_drawdown = calculate_drawdowns(results['capital'])
    pct_volatility = calculate_volatility(pct_returns, data.interval)

    return {
        ###  METADATA
        'simulation_runtime': round(end_time - start_time, 2),

        ###  STRATEGY RESULT METRICS
        'final_capital': final_capital,
        'roi': calculate_roi(initial_capital, final_capital),
        'cagr': calculate_cagr(results['capital'], interval=data.interval),
        'sharpe_ratio': calculate_sharpe_ratio(pct_returns, interval=data.interval),
        'sortino_ratio': calculate_sortino_ratio(pct_returns, interval=data.interval),
        'calmar_ratio': calculate_calmar_ratio(results['capital'], interval=data.interval),
        'pct_volatility': calculate_volatility(pct_returns, interval=data.interval),
        'profit_factor': calculate_profit_factor(periodic_upnl),
        'kurtosis': pct_returns.kurtosis(),
        'skewness': pct_returns.skew(),
        # 'pct_var': 'value at risk',

        ###  DRAWDOWN METRICS
        'drawdowns': drawdowns,
        'max_drawdown': max_drawdown,

        ###  TRADE METRICS
        # make a dataframe or table for ts
        'positions_entered': portfolio.open_trades,
        'positions_exited': portfolio.closed_trades,
        'profitable_trades': portfolio.winning_trades,
        'win_rates': win_rate,

        ###  EQUITY CURVES
        'equity_curve': equity_curve,
        'total_upnl': total_upnl,
        'periodic_upnl': periodic_upnl,
        'total_rpnl': total_rpnl,
        'periodic_rpnl': periodic_rpnl,

        ###  RETURNS METRICS
        'returns': pct_returns,
        'log_returns': log_returns,

        ###  ROLLING RATIO CURVES

        ###  CUMULATIVE RATIO CURVES
    }
