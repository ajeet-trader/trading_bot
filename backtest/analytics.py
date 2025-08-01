import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict

class Analytics:
    """
    Analyzes the results of a backtest from a portfolio history CSV file.
    """
    def __init__(self, results_path: Path):
        """
        Initializes the Analytics engine.

        Args:
            results_path (Path): The path to the backtest results CSV file.
        """
        if not results_path.exists():
            raise FileNotFoundError(f"Results file not found: {results_path}")
        
        self.results_path = results_path
        self.portfolio_history = pd.read_csv(results_path, index_col='timestamp', parse_dates=True)
        self.metrics = {}
        self.report_name = results_path.stem # e.g., "ema_crossover_AAPL_1d"

    def calculate_all_metrics(self) -> Dict:
        """Calculates a comprehensive set of performance metrics."""
        if self.portfolio_history.empty:
            return {}

        # Basic returns
        total_return = (self.portfolio_history['total'].iloc[-1] / self.portfolio_history['total'].iloc[0]) - 1
        
        # Time-based calculations
        days = (self.portfolio_history.index[-1] - self.portfolio_history.index[0]).days
        annualized_return = (1 + total_return) ** (365.25 / days) - 1 if days > 0 else 0

        # Drawdown
        rolling_max = self.portfolio_history['total'].cummax()
        drawdown = (self.portfolio_history['total'] - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        # Volatility and Sharpe Ratio
        self.portfolio_history['returns'] = self.portfolio_history['total'].pct_change().fillna(0)
        annualized_volatility = self.portfolio_history['returns'].std() * np.sqrt(252) # Assuming daily data
        sharpe_ratio = annualized_return / annualized_volatility if annualized_volatility > 0 else 0

        # Sortino Ratio (vs. downside volatility)
        downside_returns = self.portfolio_history['returns'][self.portfolio_history['returns'] < 0]
        downside_volatility = downside_returns.std() * np.sqrt(252)
        sortino_ratio = annualized_return / downside_volatility if downside_volatility > 0 else 0
        
        # Calmar Ratio
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # Trade analysis
        trades = self.portfolio_history[self.portfolio_history['signal'].isin(['BUY', 'SELL'])]
        num_trades = len(trades[trades['signal'] == 'BUY']) # Count buy signals as trades
        
        self.metrics = {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'annualized_volatility': annualized_volatility,
            'num_trades': num_trades,
        }
        return self.metrics

    def plot_equity_curve(self):
        """Generates and saves a plot of the equity curve vs. a buy-and-hold benchmark."""
        plt.style.use('seaborn-v0_8-darkgrid')
        fig, ax = plt.subplots(figsize=(14, 7))

        # Plot strategy equity
        ax.plot(self.portfolio_history.index, self.portfolio_history['total'], label='Strategy Equity', color='royalblue')

        # Plot buy-and-hold benchmark
        buy_hold_equity = self.portfolio_history['price'] / self.portfolio_history['price'].iloc[0] * self.portfolio_history['total'].iloc[0]
        ax.plot(self.portfolio_history.index, buy_hold_equity, label='Buy & Hold', color='gray', linestyle='--')

        ax.set_title(f'Equity Curve: {self.report_name}')
        ax.set_xlabel('Date')
        ax.set_ylabel('Portfolio Value ($)')
        ax.legend()
        ax.grid(True)
        
        plot_path = self.results_path.parent / f"{self.report_name}_equity.png"
        fig.savefig(plot_path)
        plt.close(fig)
        print(f"Saved equity curve plot to: {plot_path}")

    def plot_drawdown(self):
        """Generates and saves a plot of the portfolio's drawdown over time."""
        rolling_max = self.portfolio_history['total'].cummax()
        drawdown = (self.portfolio_history['total'] - rolling_max) / rolling_max

        plt.style.use('seaborn-v0_8-darkgrid')
        fig, ax = plt.subplots(figsize=(14, 7))
        
        ax.fill_between(drawdown.index, drawdown * 100, 0, color='red', alpha=0.3)
        ax.plot(drawdown.index, drawdown * 100, color='red', linewidth=1)
        
        ax.set_title(f'Drawdown Curve: {self.report_name}')
        ax.set_xlabel('Date')
        ax.set_ylabel('Drawdown (%)')
        ax.grid(True)

        plot_path = self.results_path.parent / f"{self.report_name}_drawdown.png"
        fig.savefig(plot_path)
        plt.close(fig)
        print(f"Saved drawdown plot to: {plot_path}")

    def generate_report(self):
        """Generates a full report with metrics and plots."""
        print(f"\n--- Generating Report for: {self.report_name} ---")
        self.calculate_all_metrics()
        
        # Print metrics to console
        for key, value in self.metrics.items():
            if isinstance(value, float):
                print(f"  {key.replace('_', ' ').title()}: {value:.2%}" if 'return' in key or 'drawdown' in key else f"  {key.replace('_', ' ').title()}: {value:.2f}")
            else:
                print(f"  {key.replace('_', ' ').title()}: {value}")

        # Generate plots
        self.plot_equity_curve()
        self.plot_drawdown()
        print("--- Report Generation Complete ---")

# Example usage for direct execution and testing
if __name__ == "__main__":
    # This script assumes you have already run `backtest/engine.py`
    # and have .csv files in your `backtest/results` directory.
    
    results_dir = Path(__file__).parent / "results"
    if not results_dir.exists() or not any(results_dir.iterdir()):
        print("No backtest results found. Please run `backtest/engine.py` first.")
    else:
        # Find the first CSV file and generate a report for it
        #first_result_file = next(results_dir.glob('*.csv'), None)
        first_result_file = results_dir / "ema_crossover_AAPL_1d.csv"
        if first_result_file:
            analytics_engine = Analytics(first_result_file)
            analytics_engine.generate_report()
        else:
            print("No .csv files found in the results directory.")