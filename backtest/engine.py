import sys
from pathlib import Path

# Add project root to Python path for relative imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime

from utils.config_loader import config as global_config
from data.data_storage import DataStorage
from strategies import get_strategy_class
from strategies.base_strategy import StrategyConfig

class Backtester:
    """
    A simple vectorized backtester that loads data, generates signals using strategies,
    simulates trades, and calculates performance metrics.
    """

    def __init__(self, initial_capital: float, commission: float,
                 slippage: float, risk_per_trade: float):
        """
        Initialize the backtester with key trading parameters.

        Args:
            initial_capital: Starting cash for simulation.
            commission: Commission per trade (fixed amount).
            slippage: Percentage slippage on price per trade.
            risk_per_trade: Fraction of capital risked per trade.
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.risk_per_trade = risk_per_trade
        self.data_storage = DataStorage()

        # Create directory to save backtest CSV results
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(exist_ok=True)

    def run(self, strategy_name: str, symbol: str, interval: str,
            start_date: datetime, end_date: datetime) -> Tuple[pd.DataFrame, Dict]:
        """
        Run a backtest for a particular strategy and instrument.

        Args:
            strategy_name: Name of the strategy module (must be registered).
            symbol: Trading symbol to backtest on (e.g., 'AAPL').
            interval: Data interval (e.g., '1d', '1h').
            start_date: Backtest start date (inclusive).
            end_date: Backtest end date (inclusive).

        Returns:
            portfolio_history: DataFrame with daily portfolio value and cash history.
            performance_metrics: Dictionary with metrics like Sharpe ratio, max drawdown, etc.
        """
        # Load OHLCV data for the symbol and date range
        print(f"[Backtester] Loading data for {symbol} {interval} between {start_date} and {end_date}")
        data = self.data_storage.load_data(symbol, interval, start_date, end_date)
        print(f"[Backtester] Loaded {len(data)} rows")

        if data.empty:
            raise ValueError(f"No data found for {symbol} {interval} in the given date range.")

        # Retrieve strategy configuration from global config file
        strategy_config_dict = next((s for s in global_config['strategies'] if s['name'] == strategy_name), None)
        if not strategy_config_dict:
            raise ValueError(f"Strategy '{strategy_name}' not found in config.yaml.")

        strategy_config = StrategyConfig(name=strategy_name, params=strategy_config_dict['params'])
        strategy = get_strategy_class(strategy_name)(strategy_config, symbol)
        signals = strategy.generate_signals(data)

        # If no signals, skip simulation
        if not signals:
            print(f"No signals generated for {strategy_name}. Skipping backtest.")
            return pd.DataFrame(), {}

        # Simulate portfolio performance with generated signals
        portfolio_history = self._simulate_trades(data, signals)

        # Evaluate performance metrics for the portfolio
        performance_metrics = self._calculate_performance(portfolio_history)

        # Save portfolio history to CSV for review
        results_file = self.results_dir / f"{strategy_name}_{symbol}_{interval}.csv"
        portfolio_history.to_csv(results_file)
        print(f"Saved detailed backtest results to: {results_file}")

        return portfolio_history, performance_metrics

    def _simulate_trades(self, data: pd.DataFrame, signals: List) -> pd.DataFrame:
        """
        Simulate trades based on generated signals.

        Args:
            data: OHLCV DataFrame indexed by timestamp.
            signals: List of Signal objects (must have to_dict() method or accessible attributes).

        Returns:
            portfolio: DataFrame with portfolio holdings, cash and total values over time.
        """
        # Convert signal objects to dicts for DataFrame conversion;
        # fallback to manual attribute extraction if no to_dict() available.
        try:
            signals_df = pd.DataFrame([s.to_dict() for s in signals]).set_index('timestamp')
        except AttributeError:
            signals_df = pd.DataFrame({
                'timestamp': [s.timestamp for s in signals],
                'signal_type': [s.signal_type for s in signals],
                'price': [getattr(s, 'price', None) for s in signals]
            }).set_index('timestamp')

        # Create an empty portfolio DataFrame aligned with price data index
        portfolio = pd.DataFrame(index=data.index)
        portfolio['price'] = data['close']
        portfolio['signal'] = signals_df['signal_type']
        # Left join signals to the main portfolio DataFrame to align on the index
        #portfolio = portfolio.join(signals_df['signal_type'])

        cash = self.initial_capital
        position = 0.0  # Number of shares/units held

        # Initialize portfolio columns
        portfolio['holdings'] = 0.0  # Value of holdings = position * price
        portfolio['cash'] = self.initial_capital  # Cash available
        portfolio['total'] = self.initial_capital  # Total portfolio value (cash + holdings)

        for i in range(len(portfolio)):
            signal = portfolio['signal'].iloc[i]
            #signal = portfolio['signal_type'].iloc[i]
            price = portfolio['price'].iloc[i]

            # Adjust prices for slippage on buys/sells
            buy_price = price * (1 + self.slippage)
            sell_price = price * (1 - self.slippage)

            if signal == 'BUY' and cash > 0:
                # Risk fixed fraction of cash per trade
                trade_value = cash * self.risk_per_trade
                quantity_to_buy = trade_value / buy_price
                cash -= quantity_to_buy * buy_price
                cash -= self.commission
                position += quantity_to_buy

            elif signal == 'SELL' and position > 0:
                # Sell entire position
                cash += position * sell_price
                cash -= self.commission
                position = 0.0

            # Update portfolio values for current timestamp
            portfolio.iloc[i, portfolio.columns.get_loc('holdings')] = position * price
            portfolio.iloc[i, portfolio.columns.get_loc('cash')] = cash
            portfolio.iloc[i, portfolio.columns.get_loc('total')] = cash + (position * price)

        return portfolio

    def _calculate_performance(self, portfolio: pd.DataFrame) -> Dict:
        """
        Compute performance metrics including returns, max drawdown and Sharpe ratio.

        Args:
            portfolio: DataFrame with portfolio total value over time.

        Returns:
            Dictionary of summary performance statistics.
        """
        if portfolio.empty:
            return {}

        # Total return over the backtest period
        total_return = (portfolio['total'].iloc[-1] / portfolio['total'].iloc[0]) - 1

        # Maximum drawdown calculation
        rolling_max = portfolio['total'].cummax()
        drawdown = (portfolio['total'] - rolling_max) / rolling_max
        max_drawdown = drawdown.min()

        # Daily returns and annualized statistics for Sharpe ratio
        portfolio['returns'] = portfolio['total'].pct_change().fillna(0)
        annualized_return = portfolio['returns'].mean() * 252  # trading days per year
        annualized_volatility = portfolio['returns'].std() * np.sqrt(252)
        sharpe_ratio = annualized_return / annualized_volatility if annualized_volatility > 0 else 0

        return {
            'total_return': total_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'annualized_return': annualized_return,
            'annualized_volatility': annualized_volatility
        }


if __name__ == "__main__":
    # Import strategies to ensure decorators/registering occurs before use
    import strategies.ema_crossover
    import strategies.rsi_strategy
    import strategies.bollinger_bands
    import strategies.mean_reversion

    print("--- Running Backtester Engine ---")

    backtester = Backtester(
        initial_capital=100_000.0,
        commission=1.0,      # $1 commission per trade
        slippage=0.001,      # 0.1% slippage
        risk_per_trade=0.02  # Risk 2% of capital per trade
    )

    # Find enabled strategies from config.yaml
    enabled_strategies = [s['name'] for s in global_config['strategies'] if s.get('enabled', True)]
    all_metrics = {}

    # Define backtest date range to match data available
    start_date = datetime(2020, 8, 3)
    end_date = datetime(2023, 7, 30)

    # Run backtest for all enabled strategies
    for strategy_name in enabled_strategies:
        print(f"\n--- Backtesting Strategy: {strategy_name} ---")
        try:
            _, metrics = backtester.run(
                strategy_name=strategy_name,
                symbol='AAPL',
                interval='1d',
                start_date=start_date,
                end_date=end_date
            )
            all_metrics[strategy_name] = metrics
        except Exception as e:
            print(f"Could not backtest {strategy_name}. Reason: {e}")

    # Print summary of backtest metrics
    print("\n\n--- Backtest Summary ---")
    for strategy, metrics in all_metrics.items():
        if metrics:
            print(f"\nStrategy: {strategy}")
            print(f" Total Return: {metrics['total_return']:.2%}")
            print(f" Max Drawdown: {metrics['max_drawdown']:.2%}")
            print(f" Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        else:
            print(f"\nStrategy: {strategy}\n No results generated.")
