# backtesting-engine

A modular, event-driven backtesting engine built from scratch in Python. It is designed to test quantitative trading strategies across multiple asset classes (Equities, Derivatives) with a focus on accurate execution simulation and risk management.

## 🚀 Current Status: Active Development

*Currently prototyping the core event-loop and implementing a foundational Mean Reversion Pairs Trading strategy.*

## 🏗️ Architecture Overview

The engine utilizes an Event-Driven Architecture to decouple market data, trading logic, and portfolio management. This ensures that new strategies can be tested without modifying the underlying infrastructure.

* **`DataHandler`**: Ingests historical market data (bars/ticks) and streams `MarketEvents` to the queue.
* **`Strategy`**: An abstract base class. Custom algorithms inherit from this to generate `SignalEvents` based on incoming market data.
* **`Portfolio`**: Tracks positions, cash balances, and risk metrics. Converts `SignalEvents` into `OrderEvents` subject to capital constraints.
* **`ExecutionHandler`**: Simulates exchange mechanics, factoring in estimated slippage, transaction costs, and latency to generate `FillEvents`.

## 📈 Included Strategies

1. **Mean Reversion Pairs Trading (Active)**: Analyzes the spread between two cointegrated assets, generating long/short signals when the spread deviates from its historical mean.

## 🛣️ Roadmap

* [x] Basic Event Queue implementation.
* [x] Historical CSV Data Handler for equities.
* [x] Base Strategy class and Pairs Trading implementation.
* [ ] Slippage and Commission modeling in the Execution Handler.
* [ ] Performance metrics tear-sheet (Sharpe, Max Drawdown, Calmar).
* [ ] Expand Asset Classes: Add support for Derivatives (Futures/Options) including margin tracking and contract multipliers.
* [ ] Parameter optimization grid search.

## 💻 Usage (Placeholder)

```python
from engine.data import CSVDataHandler
from engine.portfolio import Portfolio
from engine.execution import SimulatedExecution
from strategies.pairs_trade import MeanReversionPairs

# Initialize components
data = CSVDataHandler(data_dir="data/", symbols=["PEP", "KO"])
strategy = MeanReversionPairs(lookback_window=20, z_score_threshold=2.0)
portfolio = Portfolio(initial_capital=100000.0)
broker = SimulatedExecution(commission=0.001)

# Run Engine
backtester = BacktestEngine(data, strategy, portfolio, broker)
backtester.run()
backtester.output_summary_stats()
```

### engine todo

- [ ] event Architecture
- [ ]

### mean reversion pairs trading todo

- [ ] correlation and heatmap of subset of ticks
- [ ] variable inputs
- [ ] outputs (https://youtu.be/2EdRM1eLsrw)

---

*Written by BooleanCube :]*
