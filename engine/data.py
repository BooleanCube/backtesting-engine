import os
import pandas as pd
from abc import ABC, abstractmethod
from .events import Event, MarketEvent
from typing import Dict, List, Tuple, Hashable
from queue import Queue
from datetime import datetime as dt


DATA_DIR = "../data/"

class Bar:
    def __init__(self, datetime, open, high, low, close, volume):
        self.datetime: dt = datetime
        self.open: float = open
        self.high: float = high
        self.low: float = low
        self.close: float = close
        self.volume: float = volume

class DataHandler(ABC):
    @abstractmethod
    def get_latest_bar(self, symbol) -> Bar | None:
        # returns the last bar updated
        raise NotImplementedError("Should implement get_latest_bar()")

    @abstractmethod
    def get_latest_bars(self, symbol, N=1) -> List[Bar] | None:
        # returns the last N bars updated
        raise NotImplementedError("Should implement get_latest_bars)")

    @abstractmethod
    def get_latest_bar_datetime(self, symbol) -> dt | None:
        # returns a python datetime object for the last bar
        raise NotImplementedError("Should implement get_latest_bar_datetime()")

    @abstractmethod
    def update_bars(self) -> None:
        # pushes the latest bars to the latext_symbol_data structure
        raise NotImplementedError("Should implement update_bars()")

class CSVHandler(DataHandler):
    def __init__(self, events_queue, histories):
        self.events_queue: Queue[Event] = events_queue
        self.histories: List[str] = histories
        self.symbols: List[str] = [s.split("_")[0] for s in self.histories]

        self.symbol_data: Dict[str, pd.DataFrame] = {}
        self.latest_symbol_data: Dict[str, List[Bar]] = {}

        self.terminate_simulation = False
        self._open_convert_csv_files()

    def _open_convert_csv_files(self) -> None:
        for history, symbol in zip(self.histories, self.symbols):
            filepath = os.path.join(DATA_DIR, f"{history}.csv")

            self.symbol_data[symbol] = pd.read_csv(
                filepath,
                parse_dates=True,
                index_col=0
            )

            self.symbol_data[symbol].sort_index(inplace = True)
            self.latest_symbol_data[symbol] = []

        self.bar_stream = self._generate_aligned_bars()

    def _generate_aligned_bars(self):
        dfs = {s: self.symbol_data[s] for s in self.symbols}
        df_merged = pd.concat(dfs, axis=1, keys=self.symbols)

        for timestamp, row in df_merged.iterrows():
            yield timestamp, row

    def _get_next_bar(self) -> Tuple[Hashable, pd.Series] | Tuple[None, None]:
        try:
            timestamp, row = next(self.bar_stream)
            return timestamp, row
        except StopIteration:
            self.terminate_simulation = True
            return None, None

    def update_bars(self) -> None:
        timestamp, row = self._get_next_bar()
        if row is None: return

        for symbol in self.symbols:
            sym_data = row[symbol]

            if not pd.isna(sym_data['Close']):
                bar = Bar(
                    datetime = timestamp,
                    open = sym_data['Open'],
                    high = sym_data['High'],
                    low = sym_data['Low'],
                    close = sym_data['Close'],
                    volume = sym_data['Volume']
                )
                self.latest_symbol_data[symbol].append(bar)

        self.events_queue.put(MarketEvent(timestamp))

    def get_latest_bar(self, symbol) -> Bar | None:
        try:
            return self.latest_symbol_data[symbol][-1]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            return None
        except IndexError:
            return None

    def get_latest_bars(self, symbol, N=1) -> List[Bar] | None:
        try:
            return self.latest_symbol_data[symbol][-N:]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            return None
        except IndexError:
            return None

    def get_latest_bar_datetime(self, symbol) -> dt | None:
        try:
            return self.latest_symbol_data[symbol][-1].datetime
        except KeyError:
            print("That symbol is not available in the historical data set.")
            return None
        except IndexError:
            return None

