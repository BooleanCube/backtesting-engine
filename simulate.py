from queue import Queue
import time

from engine.events import Event, MarketEvent, SignalEvent, OrderEvent, FillEvent
from engine.data import CSVHandler, DataHandler
from engine.execution import ExecutionHandler, SimulatedExecution
from engine.portfolio import Portfolio
from strategies.base import Strategy
from strategies.random import Random


def run(strategy_id, datapaths, initial_capital):
    print("Initializing engine components...")

    event_loop: Queue[Event] = Queue()
    data: DataHandler = CSVHandler(events_queue=event_loop, histories=datapaths)
    portfolio: Portfolio = Portfolio(data_handler=data, events_queue=event_loop, initial_capital=initial_capital)

    strategy: Strategy
    match strategy_id:
        case 'MRP':
            # change to mean reversion pair
            strategy = Random(data_handler=data, events_queue=event_loop, symbols=data.symbols)
        case _:
            strategy = Random(data_handler=data, events_queue=event_loop, symbols=data.symbols)

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
                    strategy.calculate_signals(event)
                    portfolio.update_timeindex(event)
                case SignalEvent():
                    portfolio.generate_signal_order(event)
                case OrderEvent():
                    broker.execute_order(event)
                case FillEvent():
                    portfolio.fill_order(event)

    end_time = time.time()
    print(f"Backtest completed in {round(end_time - start_time, 2)} seconds.")

    results_df = portfolio.create_equity_curve_dataframe()
    final_equity = results_df['capital'].iloc[-1]
    total_return = ((final_equity - initial_capital) / initial_capital) * 100

    print("-" * 30)
    print("BACKTEST RESULTS")
    print("-" * 30)
    print(f"Initial Capital : ${initial_capital:,.2f}")
    print(f"Final Equity    : ${final_equity:,.2f}")
    print(f"Total Return    : {total_return:.2f}%")
