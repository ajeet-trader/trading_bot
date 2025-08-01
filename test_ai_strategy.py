#import sys
#from pathlib import Path

# Add project root to Python path for relative imports
#sys.path.append(str(Path(__file__).resolve().parent.parent))
#sys.path.append(str(Path(__file__).resolve().parent))


from backtest.engine import Backtester
from backtest.analytics import Analytics
from datetime import datetime
from pathlib import Path
# Import the new strategy to ensure it's registered
import strategies.ai_strategy
if __name__ == "__main__":
    print("--- Backtesting AI-Driven Strategy ---")
    
    # 1. Initialize the backtester
    backtester = Backtester(
        initial_capital=100_000.0,
        commission=1.0,
        slippage=0.001,
        risk_per_trade=0.02
    )
    
    # 2. Run the backtest for the AI strategy
    strategy_name = "ai_strategy"
    symbol = 'AAPL'
    interval = '1d'
    
    try:
        # We need to modify the backtester to accept param overrides
        # For now, we assume the config is set correctly in config.yaml
        portfolio_history, metrics = backtester.run(
            strategy_name=strategy_name,
            symbol=symbol,
            interval=interval,
            start_date=datetime(2022, 1, 1),
            end_date=datetime(2023, 12, 31)
        )
        
        if not portfolio_history.empty:
            print("\n--- Backtest Summary ---")
            print(f"Strategy: {strategy_name}")
            print(f"  Total Return: {metrics['total_return']:.2%}")
            print(f"  Max Drawdown: {metrics['max_drawdown']:.2%}")
            print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
            
            # 3. Generate analytics report
            results_path = Path(__file__).parent / "backtest" / "results" / f"{strategy_name}_{symbol}_{interval}.csv"
            if results_path.exists():
                analytics_engine = Analytics(results_path)
                analytics_engine.generate_report()
                print("\n✅ AI Strategy backtest and analysis complete.")
            else:
                print(f"Warning: Results file not found at {results_path}")
        else:
            print("Backtest completed but generated no trades.")
            
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print("Please ensure you have trained the required model (e.g., 'AAPL_1d_xgb') by running `model_trainer.py`.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")