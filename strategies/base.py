from abc import ABC, abstractmethod
from queue import Queue
from threading import Event

from engine.data import DataHandler

class Strategy(ABC):
    @abstractmethod
    def calculate_signals(self, event):
        # implement the strategy to send the portfolio signals
        raise NotImplementedError("Should implement calculate_signals()")
