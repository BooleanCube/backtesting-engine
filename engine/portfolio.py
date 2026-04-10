from operator import pos
from typing import Literal, Dict, List
from queue import Queue

from .data import DataHandler
from .events import Event, MarketEvent, SignalEvent, OrderEvent, FillEvent


#  TODO: implement functionality for bonds, options, futures, limit orders

class Position:
    def __init__(self, symbol, security_type, order_type, cost, quantity, direction):
        self.symbol: str = symbol
        self.security_type: Literal['EQUITY', 'BOND', 'OPTION', 'FUTURE'] = security_type
        self.order_type: Literal['MARKET', 'LIMIT'] = order_type
        self.cost: float = cost
        self.quantity: float = quantity
        self.direction: Literal['BUY', 'SELL'] = direction

class Portfolio:
    def __init__(self, data_handler, events_queue, initial_capital):
        self.data_handler: DataHandler = data_handler
        self.events_queue: Queue[Event] = events_queue
        self.capital: float = initial_capital
        self.buying_power: float = self.capital

        self.positions: Dict[str, Position] = {}

    def update_timeindex(self, event: MarketEvent) -> None:
        self.capital = self.buying_power

        for symbol in self.positions:
            position = self.positions[symbol]
            latest_bar = self.data_handler.get_latest_bar(symbol)
            if latest_bar is None: continue

            position_value = latest_bar.close * position.quantity
            self.capital += position_value

    def compute_signal(self, event: SignalEvent) -> None:
        symbol = event.symbol
        position = self.positions.get(symbol, None)
        quantity, direction = self.buying_power * event.strength, None

        if event.signal_type == 'EXIT':
            if position is None: return
            direction = 'BUY' if position.direction == 'SELL' else 'BUY'
            quantity = position.quantity
        else:
            direction = 'BUY' if event.signal_type == 'LONG' else 'SELL'

        self.events_queue.put(OrderEvent(
            symbol = symbol,
            security_type = 'EQUITY',
            order_type = 'MARKET',
            quantity = quantity,
            direction = direction
        ))

    def fill_order(self, event: FillEvent) -> None:
        pass
