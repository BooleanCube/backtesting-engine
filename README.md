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

* [X] Basic Event Queue implementation.
* [X] Historical CSV Data Handler for equities.
* [X] Test backtesting engine simulation.
* [ ] Performance metrics tear-sheet (sharpe ratio, max drawdown, calmar, profit factor, sortino ratio, win rate, roi, watch video for more).
* [ ] Mean Reversion Pairs Trading Strategy implementation.
* [ ] Slippage and Commission modeling in the Execution Handler.
* [ ] Expand Asset Classes: Add support for Derivatives (Futures/Options) including margin tracking and contract multipliers.
* [ ] Handle other types of orders (stop loss, limit, etc.)
* [ ] Parameter optimization grid search.

### todo

- [ ] study sharpe ratio, and other quant metrics, and implement
- [X] fix up randomized trading page in terms of data selection and visualization
- [ ] study up and fix portfolio management for short selling
- [ ] fix up simulation results to measure quant metrics
- [ ] start working on mean reversion pair trading strategy

### mean reversion pairs trading todo

- [ ] correlation and heatmap of subset of ticks
- [ ] variable inputs
- [ ] outputs (https://youtu.be/2EdRM1eLsrw)

---

*Written by BooleanCube :]*

---

## NOTES TO SELF

```
The `ExecutionHandler` might seem like an unnecessary extra step right now—especially when our current simulator just instantly turns an `OrderEvent` into a `FillEvent`—but it is arguably the most critical component for preventing your backtests from lying to you.

### The Main Purpose
The main purpose of the `ExecutionHandler` is to act as the **bridge between your trading intent and market reality**. 

Your `Strategy` generates an idea ("Buy Apple"). Your `Portfolio` sizes the idea based on your cash ("Buy 100 shares of Apple"). But the `ExecutionHandler` determines **what actually happens** when that order hits the exchange ("You only bought 40 shares because liquidity dried up, and you paid $0.05 more per share than you expected").

By strictly separating this from your strategy and portfolio, you encapsulate all the chaotic, unfair realities of the actual stock market into one isolated module.

### Why Separation Matters: Real-World Examples

Here are three scenarios where having a standalone `ExecutionHandler` saves a quantitative trading system from catastrophic failure.

#### 1. The "Flipping the Switch" Scenario (Live Trading)
The most practical reason to separate the `ExecutionHandler` is so you can take your backtesting engine into live markets without rewriting your code.

* **In Backtesting:** You use a `SimulatedExecutionHandler`. It reads historical CSV data, estimates a tiny bit of slippage, and spits out a `FillEvent`.
* **In Live Trading:** You completely delete the `SimulatedExecutionHandler` and plug in an `InteractiveBrokersExecutionHandler`. This new handler takes the exact same `OrderEvent` from your portfolio, translates it into an API request, sends it to the broker over the internet, listens for a webhook response, and generates a `FillEvent` when the real trade clears. 

Because of the separation of concerns, your complex Mean Reversion strategy and your intricate Portfolio risk math never even know they transitioned from a CSV file to the live stock market. 

#### 2. Modeling Market Impact and Slippage
Imagine you are testing a high-frequency pairs trading strategy that trades thousands of times a day.

If your portfolio module just assumes you buy exactly at the closing price of the bar, your backtest will show you making millions of dollars. In reality, every time you send a market order, you cross the bid-ask spread (slippage). If you trade large sizes, your own order will push the price of the asset away from you (market impact).

By having a separate `ExecutionHandler`, you can build complex mathematical models inside it to simulate this friction. 
* **Example:** You can program the `ExecutionHandler` to look at the `volume` of the current historical bar. If your order size is more than 1% of the bar's volume, the handler artificially penalizes your execution price by 0.2% to simulate market impact. Your strategy remains mathematically pure, while the handler enforces reality.

#### 3. Handling Partial Fills and Queue Position
Let’s say you want to trade micro-cap stocks or illiquid derivatives. Your portfolio generates an `OrderEvent` to buy 5,000 shares of a thinly traded asset at a Limit price.

In a naive engine without an execution handler, the system just assumes all 5,000 shares were bought. But what if there were only 1,000 shares available at that price? 
* A sophisticated `ExecutionHandler` will model the Limit Order Book. It will take your `OrderEvent`, see that only 1,000 shares are available, and emit a `FillEvent` for **1,000 shares**. 
* Your `Portfolio` receives this partial fill, updates its cash correctly, and leaves the other 4,000 shares pending. 

If this logic was tangled up inside your `Strategy` or `Portfolio` files, your codebase would become an unreadable mess of edge-cases and loop conditions. Isolating it keeps the engine modular and scalable.
```

