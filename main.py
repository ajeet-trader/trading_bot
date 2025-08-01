from utils.logger_setup import get_logger

error_logger = get_logger("error")
error_logger.info("Application starting up.", extra={"extra_data": {"version": "0.1.0"}})

import argparse
import json
import subprocess
from pathlib import Path
from datetime import datetime
# Adjust sys.path to ensure all project modules are importable
# This allows running main.py from the project root
import sys
project_root_path = Path(__file__).resolve().parent
if str(project_root_path) not in sys.path:
    sys.path.insert(0, str(project_root_path)) # Insert at the beginning for priority
# Import global configuration
from utils.config_loader import config
# Import all top-level modules for orchestration
from autotrain.retrainer import AutoRetrainer
from backtest.engine import Backtester
from execution.live_integration import LiveTrader, AlpacaAdapter
from execution.risk_manager import RiskManager
from utils.data_structures import Signal # For creating mock signals in live mode
# Import all strategy modules to ensure they are registered with the framework
# This makes them discoverable by name (e.g., 'ema_crossover', 'ai_strategy')
import strategies.ema_crossover
import strategies.rsi_strategy
import strategies.bollinger_bands
import strategies.mean_reversion
import strategies.ai_strategy
class MainApp:
    """
    The main controller for the AI Trading Bot Command Line Interface (CLI).
    Orchestrates different operational modes of the trading system.
    """
    def __init__(self):
        """Initializes the MainApp with access to the global configuration."""
        self.config = config
    def run_retrain(self, symbol: str, interval: str):
        """
        Runs the full model retraining pipeline for a specified symbol and interval.
        This fetches new data, re-engineers features, and trains/saves new models.
        """
        print(f"\n--- Initiating Model Retraining for {symbol} ({interval}) via CLI ---")
        # Parameters for the retrainer come from a sensible default or config
        retrainer = AutoRetrainer(
            retrain_schedule_days=self.config.get('autotrain', {}).get('retrain_schedule_days', 30),
            performance_threshold=self.config.get('autotrain', {}).get('performance_threshold', 0.10)
        )
        retrainer.run_retraining_pipeline(symbol, interval)
        print(f"\n--- Retraining complete for {symbol} ({interval}) ---")
    def run_backtest(self, strategy_name: str, symbol: str, interval: str):
        """
        Runs a backtest for a specific strategy on historical data.
        The backtest period is currently hardcoded for demonstration.
        """
        print(f"\n--- Starting Backtest for Strategy: '{strategy_name}' on Symbol: '{symbol}' ({interval}) ---")
        
        # Initialize Backtester with parameters from config
        backtester = Backtester(
            initial_capital=self.config['system']['initial_capital'],
            commission=self.config['system']['commission'],
            slippage=self.config['system']['slippage'],
            risk_per_trade=self.config['system']['risk_per_trade']
        )
        
        # Define the backtest period (could be configurable via CLI args too)
        # Using 2 years of data for a typical backtest
        end_date = datetime(2023, 12, 31)
        start_date = datetime(2022, 1, 1)
        try:
            portfolio_history, metrics = backtester.run(
                strategy_name=strategy_name,
                symbol=symbol,
                interval=interval,
                start_date=start_date,
                end_date=end_date
            )
            print("\n--- Backtest Summary ---")
            print(json.dumps(metrics, indent=2))
            
            # Optionally generate analytics report immediately after backtest
            from backtest.analytics import Analytics
            results_file = Path("backtest") / "results" / f"{strategy_name}_{symbol}_{interval}.csv"
            if results_file.exists():
                analytics_engine = Analytics(results_file)
                analytics_engine.generate_report()
            else:
                print(f"Warning: Backtest results file not found at {results_file}. Cannot generate full report.")
        except Exception as e:
            print(f"Error during backtest: {e}")
            import traceback
            traceback.print_exc()
        print(f"\n--- Backtest finished for {strategy_name} on {symbol} ---")
    def run_live(self):
        """
        Starts the simplified live trading loop.
        NOTE: This is a placeholder for a true, long-running, event-driven live system.
        For demonstration, it processes one mock signal.
        """
        print("\n--- Starting Live Trading Engine ---")
        print("NOTE: This is a simplified demonstration loop. A production system would be a long-running, event-driven process.")
        
        try:
            # Initialize Alpaca Adapter with keys from config
            alpaca_adapter = AlpacaAdapter(
                api_key=self.config['api_keys']['alpaca_api_key'],
                api_secret=self.config['api_keys']['alpaca_api_secret'],
                paper=True # Always default to paper for safety in example
            )
            
            # Initialize RiskManager with parameters from config
            risk_manager = RiskManager(**self.config['risk_management'])
            
            # Initialize LiveTrader
            live_trader = LiveTrader(adapter=alpaca_adapter, risk_manager=risk_manager)
            
            # --- Mock Signal Processing ---
            # In a real live system, this would be a loop that fetches new data,
            # generates signals, and passes them to live_trader.process_signal()
            print("\nAttempting to process one mock BUY signal for AAPL...")
            mock_symbol = 'AAPL'
            latest_price = alpaca_adapter.get_latest_price(mock_symbol)
            
            if latest_price > 0:
                mock_signal = Signal(
                    timestamp=datetime.now(),
                    symbol=mock_symbol,
                    strategy='manual_cli_test', # Label for this test
                    signal_type='BUY',
                    price=latest_price,
                    confidence=0.9 # High confidence for testing
                )
                live_trader.process_signal(mock_signal)
                
                print("\n--- Live Test Summary ---")
                print("Check your Alpaca paper trading account and logs/trades.log for results.")
                print("Open Positions:")
                print(alpaca_adapter.get_open_positions())
            else:
                print(f"Could not fetch live price for {mock_symbol}. Skipping mock trade.")
        except KeyError as e:
            print(f"ERROR: Missing API key or risk management parameter in your configuration: {e}.")
            print("Please ensure your config.yaml and .env files are correctly set up.")
        except Exception as e:
            print(f"An unexpected error occurred during live trading setup: {e}")
            import traceback
            traceback.print_exc() # Print full traceback for debugging
    def run_dashboard(self):
        """
        Launches the Streamlit monitoring dashboard.
        This command needs Streamlit to be installed and accessible.
        """
        print("\n--- Launching Streamlit Monitoring Dashboard ---")
        
        # Path to the dashboard script relative to main.py
        dashboard_script_path = project_root_path / "live_signals" / "dashboard.py"
        
        if not dashboard_script_path.exists():
            print(f"Error: Dashboard script not found at {dashboard_script_path}")
            print("Please ensure 'live_signals/dashboard.py' exists.")
            return
        
        try:
            # Use subprocess to run streamlit, as it runs its own server
            print(f"Running command: streamlit run {dashboard_script_path}")
            subprocess.run(["streamlit", "run", str(dashboard_script_path)], check=True)
        except FileNotFoundError:
            print("\nError: 'streamlit' command not found.")
            print("Please make sure Streamlit is installed: 'pip install streamlit'")
            print("And that 'streamlit' is in your system's PATH.")
        except subprocess.CalledProcessError as e:
            print(f"\nError running Streamlit dashboard: {e}")
            print("Check Streamlit output above for more details.")
        except Exception as e:
            print(f"An unexpected error occurred while launching dashboard: {e}")
            import traceback
            traceback.print_exc()
# --- Main Execution Block for CLI ---
if __name__ == "__main__":
    # Configure the argument parser for CLI
    parser = argparse.ArgumentParser(
        description="Sapiens AI Trading Bot Command Line Interface",
        formatter_class=argparse.RawTextHelpFormatter # Preserve newlines in help
    )
    
    # Define main commands
    parser.add_argument(
        'command', 
        choices=['retrain', 'backtest', 'live', 'dashboard'], 
        help="""Choose a command to execute:
  retrain    : Retrain AI models with fresh data.
  backtest   : Run a strategy backtest on historical data.
  live       : Start the live trading engine (simplified for demo).
  dashboard  : Launch the web-based monitoring dashboard.
"""
    )
    
    # Optional arguments common to some commands
    parser.add_argument(
        '--strategy', 
        type=str, 
        help="Required for 'backtest' command. Name of the strategy to test (e.g., 'ema_crossover', 'ai_strategy')."
    )
    parser.add_argument(
        '--symbol', 
        type=str, 
        default='AAPL', # Default symbol for convenience
        help="The trading symbol to operate on (e.g., 'AAPL', 'BTC/USDT'). Default: AAPL"
    )
    parser.add_argument(
        '--interval', 
        type=str, 
        default='1d', # Default interval for convenience
        help="The data interval to use (e.g., '1d', '1h', '5m'). Default: 1d"
    )
    
    # Parse arguments provided by the user
    args = parser.parse_args()
    
    # Initialize the main application controller
    app = MainApp()
    
    # Execute the chosen command
    if args.command == 'retrain':
        app.run_retrain(args.symbol, args.interval)
    elif args.command == 'backtest':
        if not args.strategy:
            parser.error("The '--strategy' argument is required for the 'backtest' command.")
        app.run_backtest(args.strategy, args.symbol, args.interval)
    elif args.command == 'live':
        app.run_live()
    elif args.command == 'dashboard':
        app.run_dashboard()