from abc import ABC, abstractmethod
from queue import Queue

from engine.data import DataHandler
from engine.events import Event, OrderEvent, FillEvent

class ExecutionHandler(ABC):
    @abstractmethod
    def execute_order(self, order: OrderEvent) -> None:
        # takes an OrderEvent and executes it, pushing a FillEvent into the event loop
        raise NotImplementedError("Should implement execute_order()")


class SimulatedExecution(ExecutionHandler):
    def __init__(self, data_handler, events_queue):
        self.data_handler: DataHandler = data_handler
        self.events_queue: Queue[Event] = events_queue


    def execute_order(self, order: OrderEvent) -> None:
        latest_bar = self.data_handler.get_latest_bar(order.symbol)
        if latest_bar is None: return

        fill = FillEvent(
            timeindex = latest_bar.datetime,
            symbol = order.symbol,
            exchange = 'NASDAQ',
            quantity = order.quantity,
            direction = order.direction,
            fill_cost = order.quantity * latest_bar.close
        )

        self.events_queue.put(fill)


