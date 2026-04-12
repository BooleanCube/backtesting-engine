from datetime import datetime as dt
import time
from typing import Literal
from enum import StrEnum

class EventType(StrEnum):
    MARKET = 'MARKET'
    SIGNAL = 'SIGNAL'
    ORDER = 'ORDER'
    FILL = 'FILL'

class Event:
    def __init__(self):
        self.event_type: EventType

class MarketEvent(Event):
    def __init__(self, datetime):
        self.event_type: EventType = EventType.MARKET
        self.datetime: dt = datetime
    
    def __str__(self):
        return f"MarketEvent: {self.datetime}"

class SignalEvent(Event):
    def __init__(self, strategy_id, symbol, datetime, signal_type, strength=1.0):
        self.event_type: EventType = EventType.SIGNAL
        self.strategy_id: str = strategy_id
        self.symbol: str = symbol
        self.datetime: dt = datetime
        self.signal_type: Literal['LONG', 'SHORT', 'EXIT'] = signal_type
        self.strength: float = strength

    def __str__(self):
        return f"SignalEvent: {self.symbol} | {self.signal_type} | Strength: {self.strength}"

class OrderEvent(Event):
    def __init__(self, symbol, security_type, order_type, quantity, direction):
        self.event_type: EventType = EventType.ORDER
        self.symbol: str = symbol
        self.security_type: Literal['EQUITY', 'BOND', 'OPTION', 'FUTURE'] = security_type
        self.order_type: Literal['MARKET', 'LIMIT'] = order_type
        self.quantity: float = quantity
        self.direction: Literal['BUY', 'SELL'] = direction

    def __str__(self):
        return f"OrderEvent: {self.symbol} | {self.order_type} | Quantity: {self.quantity} | Direction: {self.direction}"

    def print_order(self) -> None:
        print(f"Order: Symbol={self.symbol}, Type={self.order_type}, "
              f"Quantity={self.quantity}, Direction={self.direction}")

class FillEvent(Event):
    def __init__(self, timeindex, symbol, exchange, quantity, direction, fill_cost, commission=None):
        self.event_type: EventType = EventType.FILL
        self.timeindex: dt = timeindex
        self.symbol: str = symbol
        self.exchange: str = exchange
        self.quantity: float = quantity
        self.direction: Literal['BUY', 'SELL'] = direction
        self.fill_cost: float = fill_cost

        if commission is None: self.commission: float = self.calculate_ib_commission()
        else: self.commission: float = commission
    
    def __str__(self):
        return f"FillEvent: {self.symbol} | {self.direction} | Quantity: {self.quantity} | Fill Cost: {self.fill_cost} | Commission: {self.commission}"

    def calculate_ib_commission(self) -> float:
        """
        Calculates the fees of trading based on an Interactive Brokers fee structure for US Equities.
        1.3 is the minimum commission per trade
        """
        #  TODO: Expand for other asset classes (only works for US equities)
        full_cost = max(1.3, [0.008, 0.013][int(self.quantity <= 500)] * self.quantity)
        return full_cost

