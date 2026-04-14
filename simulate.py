from queue import Queue
import time

from engine.events import Event, MarketEvent, SignalEvent, OrderEvent, FillEvent
from engine.data import CSVHandler, DataHandler
from engine.execution import ExecutionHandler, SimulatedExecution
from engine.portfolio import Portfolio
from strategies.base import Strategy
from strategies.randomized import Randomized
from utils.performance import calculate_calmar_ratio, calculate_drawdowns, calculate_profit_factor, \
    calculate_roi, calculate_sharpe_ratio, calculate_sortino_ratio


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

    results_df = portfolio.get_results_dataframe()
    final_capital = results_df['capital'].iloc[-1]
    roi = calculate_roi(initial_capital, final_capital)
    sharpe_ratio = calculate_sharpe_ratio(results_df['returns'], interval=data.interval)
    sortino_ratio = calculate_sortino_ratio(results_df['returns'], interval=data.interval)
    calmar_ratio = calculate_calmar_ratio(results_df['capital'], interval=data.interval)
    profit_factor = calculate_profit_factor(results_df['periodic_pnl'])
    drawdowns, max_drawdown = calculate_drawdowns(results_df['capital'])
    win_rate = results_df['win_rate'].iloc[-1]

    return {
        'final_capital': final_capital,
        'roi': roi,
        'sharpe_ratio': sharpe_ratio,
        'sortino_ratio': sortino_ratio,
        'calmar_ratio': calmar_ratio,
        'profit_factor': profit_factor,
        'max_drawdown': max_drawdown,
        'win_rate': win_rate
    }
