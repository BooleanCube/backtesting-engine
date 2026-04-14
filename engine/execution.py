from abc import ABC, abstractmethod
from queue import Queue

from engine.data import DataHandler
from engine.events import Event, OrderEvent, FillEvent

class ExecutionHandler(ABC):
    @abstractmethod
    def execute_order(self, order: OrderEvent) -> None:
        # takes an OrderEvent and executes it, pushing a FillEvent into the event loop
        raise NotImplementedError("Should implement execute_order()")


#  TODO: a lot of studying to be done to accurately simulate slippage, partial fills, market impact, etc.
#        also need to implement limit orders and stop orders.
#        also need to figure out available liquidity of the market for partial fills and maybe splitting orders
#        into smaller chunks throughout the day like voloridge does.
class SimulatedExecution(ExecutionHandler):
    def __init__(self, data_handler, events_queue):
        self.data_handler: DataHandler = data_handler
        self.events_queue: Queue[Event] = events_queue


    def execute_order(self, order: OrderEvent) -> None:
        latest_bar = self.data_handler.get_latest_bar(order.symbol)
        if latest_bar is None:
            print(f"No market data available for {order.symbol}. Order cannot be executed.")
            return

        # # Simulate partial fills based on available liquidity
        # available_liquidity = latest_bar.volume * 0.1  # Assume 10% of volume is available for the order
        # fill_quantity = min(order.quantity, available_liquidity)

        # if fill_quantity < order.quantity:
        #     print(f"Partial fill for {order.symbol}: {fill_quantity}/{order.quantity} shares filled.")

        fill = FillEvent(
            timeindex = latest_bar.datetime,
            symbol = order.symbol,
            exchange = 'NASDAQ',
            quantity = order.quantity,
            direction = order.direction,
            fill_cost = order.quantity * latest_bar.close
        )

        self.events_queue.put(fill)


