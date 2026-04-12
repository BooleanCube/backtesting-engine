from numpy import random
from queue import Queue
from typing import List, Dict

from engine.events import Event
from engine.data import DataHandler
from engine.events import MarketEvent, SignalEvent
from strategies.base import Strategy


class Randomized(Strategy):
    """
    A very basic testing strategy that randomly goes LONG, SHORT, or does nothing.
    Created to test simulation logic and handler functioning.
    """
    def __init__(self, data_handler, events_queue):
        self.data_handler: DataHandler = data_handler
        self.events_queue: Queue[Event] = events_queue
        self.symbols: List[str] = data_handler.symbols
        self.invested: Dict[str, int] = {symbol: 0 for symbol in self.symbols}

    def calculate_signals(self, event: MarketEvent):
        for symbol in self.symbols:
            bars = self.data_handler.get_latest_bars(symbol, N=1)

            if bars is not None and len(bars) > 0:
                timestamp = bars[0].datetime
                random_signal = random.random()

                if random_signal > 0.90 and not self.invested[symbol]:
                    signal = SignalEvent(
                        strategy_id = 'RANDOM',
                        symbol = symbol,
                        datetime = timestamp,
                        signal_type = 'LONG',
                        strength = 0.50
                    )
                    self.events_queue.put(signal)
                    self.invested[symbol] = 1

                elif random_signal < 0.10 and self.invested[symbol]:
                    signal = SignalEvent(
                        strategy_id = 'RANDOM',
                        symbol = symbol,
                        datetime = timestamp,
                        signal_type = 'EXIT',
                    )
                    self.events_queue.put(signal)
                    self.invested[symbol] = 0
