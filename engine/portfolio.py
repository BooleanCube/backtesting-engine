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
        self.history: List[Holding] = [self.holdings]


    def update_timeindex(self, market: MarketEvent) -> None:
        latest_datetime = market.datetime

        dh = Holding(
            positions = self.holdings.positions.copy(),
            datetime = latest_datetime,
            cash = self.holdings.cash,
            commission = self.holdings.commission,
            capital = self.holdings.capital
        )

        for symbol in self.holdings.positions:
            position = self.holdings.positions[symbol]
            latest_bar = self.data_handler.get_latest_bar(symbol)
            if latest_bar is None: continue

            market_value = position.quantity * latest_bar.close
            dh.positions[symbol].value = market_value
            dh.capital += market_value

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
            order.quantity = self.holdings.cash * signal.strength
            if signal.signal_type == 'LONG': order.direction = 'BUY'
            elif signal.signal_type == 'SHORT': order.direction = 'SELL'
            else: return
        elif signal.signal_type == 'EXIT':
            quantity = position.quantity
            order.quantity = abs(quantity)
            if quantity > 0: order.direction = 'SELL'
            elif quantity < 0: order.direction = 'BUY'

        self.events_queue.put(order)


    def fill_order(self, fill: FillEvent) -> None:
        latest_bar = self.data_handler.get_latest_bar(fill.symbol)
        direction = 1 if fill.direction == 'BUY' else -1

        if latest_bar is None: return

        quantity = direction * fill.quantity
        cost = quantity * latest_bar.close
        self.holdings.positions[fill.symbol].quantity += quantity
        self.holdings.positions[fill.symbol].value += cost
        self.holdings.commission += fill.commission
        self.holdings.cash -= (cost + fill.commission)


    def create_equity_curve_dataframe(self):
        history = [holdings.to_dict() for holdings in self.history]
        curve = pd.DataFrame(history)
        curve.set_index('datetime', inplace = True)
        curve['returns'] = curve['capital'].pct_change()
        curve['equity_curve'] = (1.0 + curve['returns']).cumprod()
        return curve


