"""
engine/__init__.py

Exposes the core components of the backtesting infrastructure.
"""

# Import the events we just created
from .events import Event, EventType, MarketEvent, SignalEvent, OrderEvent, FillEvent
from .data import DataHandler, CSVHandler, Bar
from .portfolio import Portfolio, Position, Holding
from .execution import ExecutionHandler, SimulatedExecution
