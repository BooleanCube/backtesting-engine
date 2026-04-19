import copy
import numpy as np
import math
from queue import Queue
from datetime import datetime as dt
import pandas as pd
from typing import Literal, Dict, List

from .data import DataHandler
from .events import Event, MarketEvent, SignalEvent, OrderEvent, FillEvent


#  TODO: implement functionality for bonds, options, futures, limit orders

class Position:
    def __init__(self, symbol, security_type, order_type, quantity, value):
        self.symbol: str = symbol
        self.security_type: Literal['EQUITY', 'BOND', 'OPTION', 'FUTURE'] = security_type
        self.order_type: Literal['MARKET', 'LIMIT'] = order_type
        self.quantity: float = quantity # negative for short, positive for long
        self.value: float = value
        self.cost: float = value


class Holding:
    def __init__(self, positions, datetime, cash, commission, capital):
        self.positions: Dict[str, Position] = positions
        self.datetime: dt = datetime
        self.cash: float = cash
        self.commission: float = commission
        self.capital: float = capital

    def to_dict(self):
        holding_dict = {
            'datetime': self.datetime,
            'cash': self.cash,
            'commission': self.commission,
            'capital': self.capital
        }
        for symbol in self.positions: holding_dict[symbol] = vars(self.positions[symbol])

        return holding_dict


class Portfolio:
    def __init__(self, data_handler, events_queue, initial_capital):
        self.data_handler: DataHandler = data_handler
        self.events_queue: Queue[Event] = events_queue
        self.capital: float = initial_capital
        self.buying_power: float = self.capital

        self.holdings: Holding = Holding(
            positions = {},
            datetime = None,
            cash = initial_capital,
            commission = 0.0,
            capital = initial_capital
        )
        self.history: List[Holding] = [copy.deepcopy(self.holdings)]

        self.winning_trades, self.open_trades, self.closed_trades = 0, 0, 0


    def update_timeindex(self, market: MarketEvent) -> None:
        latest_datetime = market.datetime

        self.holdings.capital = self.holdings.cash

        for symbol in self.holdings.positions:
            position = self.holdings.positions[symbol]
            latest_bar = self.data_handler.get_latest_bar(symbol)
            if latest_bar is None: continue

            market_value = position.quantity * latest_bar.close
            position.value = market_value
            self.holdings.capital += market_value
        
        dh = Holding(
            positions = copy.deepcopy(self.holdings.positions),
            datetime = latest_datetime,
            cash = self.holdings.cash,
            commission = self.holdings.commission,
            capital = self.holdings.capital
        )

        self.history.append(dh)


    # currently a very naive version that only handles US equities and market orders
    #  TODO: currently only spends a ratio of the cash indicated by strength, compute complex risk sizing isntead
    def generate_signal_order(self, signal: SignalEvent) -> None:
        position = self.holdings.positions.get(signal.symbol, None)
        order = OrderEvent(
            symbol = signal.symbol,
            security_type = 'EQUITY',
            order_type = 'MARKET',
            quantity = 0,
            direction = 'BUY'
        )

        if position is None:
            latest_bar = self.data_handler.get_latest_bar(signal.symbol)
            if latest_bar is None: return
            order.quantity = math.floor(self.holdings.cash * signal.strength / latest_bar.close * 100) / 100.0
            if signal.signal_type == 'LONG': order.direction = 'BUY'
            elif signal.signal_type == 'SHORT': order.direction = 'SELL'
            else: return
        elif signal.signal_type == 'EXIT':
            quantity = position.quantity
            order.quantity = abs(quantity)
            if quantity > 0: order.direction = 'SELL'
            elif quantity < 0: order.direction = 'BUY'

        self.events_queue.put(order)


    def set_default_position(self, symbol):
        if symbol not in self.holdings.positions: self.open_trades += 1

        return self.holdings.positions.setdefault(symbol, Position(
            symbol = symbol,
            security_type = 'EQUITY',
            order_type = 'MARKET',
            quantity = 0,
            value = 0
        ))


    #  TODO: check for sufficient buying power, margin requirements, position limits, etc. before placing order
    #  TODO: im not sure if short selling is being handled correctly in terms of cash and buying power, need to review and test more
    def fill_order(self, fill: FillEvent) -> None:
        latest_bar = self.data_handler.get_latest_bar(fill.symbol)
        if latest_bar is None: return
        direction = 1 if fill.direction == 'BUY' else -1

        quantity = direction * fill.quantity
        cost = quantity * latest_bar.close
        position = self.set_default_position(fill.symbol)
        position.quantity += quantity
        position.value += cost
        position.cost += cost
        self.holdings.commission += fill.commission
        self.holdings.cash -= (cost + fill.commission)
        self.holdings.capital -= fill.commission

        # exiting position
        if abs(position.quantity) < 1e-6:
            self.closed_trades += 1
            if position.cost < position.value: self.winning_trades += 1

            self.holdings.cash += position.value
            del self.holdings.positions[fill.symbol]


    def get_results_dataframe(self):
        history = [holdings.to_dict() for holdings in self.history]
        result = pd.DataFrame(history)
        result.set_index('datetime', inplace = True)
        return result

