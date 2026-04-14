import os
import pandas as pd
from abc import ABC, abstractmethod
from .events import Event, MarketEvent
from typing import Dict, List, Tuple, Hashable
from queue import Queue
from datetime import datetime as dt


DATA_DIR = "./data/"

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
    def __init__(self, events_queue, selected_histories):
        self.events_queue: Queue[Event] = events_queue
        self.histories: List[str] = selected_histories
        self.interval: str = self.histories[0].split("_")[1] if self.histories else None
        self.symbols: List[str] = list(set(map(lambda s: s.split("_")[0], self.histories)))

        self.symbol_data: Dict[str, pd.DataFrame] = {}
        self.latest_symbol_data: Dict[str, List[Bar]] = {}

        self.terminate_simulation = False
        self._open_convert_csv_files()


    def _open_convert_csv_files(self) -> None:
        temp_symbol_data = {symbol: [] for symbol in self.symbols}

        # 1. Load all files and group them by their base symbol
        for history in self.histories:
            try:
                symbol = history.split("_")[0]
                filepath = os.path.join(DATA_DIR, f"{history}.csv")

                if not os.path.exists(filepath):
                    print(f"File not found: {filepath}")
                    continue

                df = pd.read_csv(
                    filepath,
                    parse_dates=True,
                    index_col=0
                )

                if df.empty or not all(col in df.columns for col in ['Open', 'High', 'Low', 'Close', 'Volume']):
                    print(f"Malformed or empty data in file: {filepath}")
                    continue

                df.index = pd.to_datetime(df.index, utc=True)
                temp_symbol_data[symbol].append(df)

            except Exception as e:
                print(f"Error processing {history}: {e}")

        # 2. Combine, sort, and clean the data for each symbol
        for symbol in temp_symbol_data:
            combined_df = pd.concat(temp_symbol_data[symbol], ignore_index=False)
            combined_df.sort_index(inplace=True)
            combined_df = combined_df[~combined_df.index.duplicated(keep='first')]

            self.symbol_data[symbol] = combined_df
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

