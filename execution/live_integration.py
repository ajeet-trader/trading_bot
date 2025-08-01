import sys
from pathlib import Path

# Add project root to Python path for relative imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import URL  # Correct import for URL
from utils.data_structures import Signal  # Import our Signal dataclass
from utils.logger_setup import get_logger  # Import our logging utility
from execution.risk_manager import RiskManager  # Import our RiskManager
from dataclasses import asdict

# --- Abstract Broker Interface ---
class BaseLiveAdapter(ABC):
    """
    Abstract base class defining the interface for all live trading adapters.
    Any concrete brokerage integration must implement these methods.
    """
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def place_order(self, symbol: str, order_type: str, quantity: float, side: str) -> Dict[str, Any]:
        """
        Places a trade order with the brokerage.
        Args:
            symbol (str): The symbol to trade (e.g., 'AAPL', 'BTC/USDT').
            order_type (str): The type of order (e.g., 'market', 'limit').
            quantity (float): The amount to trade (shares for stocks, base currency for crypto).
            side (str): The trade side ('buy' or 'sell').
        Returns:
            Dict[str, Any]: A dictionary containing the order confirmation or error details from the broker.
        """
        pass

    @abstractmethod
    def get_open_positions(self) -> List[Dict[str, Any]]:
        """
        Retrieves a list of all currently open positions from the brokerage account.
        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each representing an open position.
        """
        pass

    @abstractmethod
    def get_account_balance(self) -> Dict[str, Any]:
        """
        Retrieves comprehensive account balance and equity information.
        Returns:
            Dict[str, Any]: A dictionary with account details (e.g., 'equity', 'cash', 'buying_power').
        """
        pass

    @abstractmethod
    def get_latest_price(self, symbol: str) -> float:
        """
        Gets the latest market price (last traded price) for a given symbol.
        Args:
            symbol (str): The symbol for which to get the price.
        Returns:
            float: The latest traded price. Returns 0.0 if price cannot be fetched.
        """
        pass

# --- Concrete Implementation Example: AlpacaAdapter ---
class AlpacaAdapter(BaseLiveAdapter):
    """
    A concrete implementation of BaseLiveAdapter for the Alpaca Trading API.
    Uses alpaca-trade-api library.
    """
    def __init__(self, api_key: str, api_secret: str, paper: bool = True):
        """
        Initializes the AlpacaAdapter.
        Args:
            api_key (str): Alpaca API Key ID.
            api_secret (str): Alpaca API Secret Key.
            paper (bool): If True, connects to the Alpaca paper trading environment; otherwise, live.
        """
        super().__init__("Alpaca")
        
        # Determine the base URL for paper or live trading
        base_url = URL('https://paper-api.alpaca.markets' if paper else 'https://api.alpaca.markets')
        self.api = tradeapi.REST(key_id=api_key, secret_key=api_secret, base_url=base_url)
        
        try:
            # Verify connection by fetching account details
            account = self.api.get_account()
            print(f"Successfully connected to Alpaca {'Paper' if paper else 'Live'} Account: {account.account_number}, Status: {account.status}")
        except Exception as e:
            print(f"Error connecting to Alpaca: {e}")
            raise  # Re-raise the exception to indicate connection failure

    def place_order(self, symbol: str, order_type: str, quantity: float, side: str) -> Dict[str, Any]:
        """Places a trade order with Alpaca."""
        try:
            # Alpaca API expects integer quantities for stocks if not fractional enabled
            # Ensure quantity is a positive number and cast to int if needed for whole shares
            qty = max(1, int(quantity))  # For simplicity, ensure at least 1 share and integer
            
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type=order_type,
                time_in_force='gtc'  # Good 'til canceled
            )
            print(f"Placed {side.upper()} order for {qty} of {symbol} via Alpaca.")
            return order._raw  # Return the raw dictionary response from Alpaca
        except Exception as e:
            print(f"Error placing order with Alpaca for {symbol}: {e}")
            return {'error': str(e), 'symbol': symbol, 'quantity': quantity, 'side': side}

    def get_open_positions(self) -> List[Dict[str, Any]]:
        """Retrieves a list of all open positions from Alpaca."""
        try:
            positions = self.api.list_positions()
            return [p._raw for p in positions]  # Convert Alpaca objects to dictionaries
        except Exception as e:
            print(f"Error getting open positions from Alpaca: {e}")
            return []

    def get_account_balance(self) -> Dict[str, Any]:
        """Retrieves account balance and equity information from Alpaca."""
        try:
            account = self.api.get_account()
            return account._raw  # Convert Alpaca object to dictionary
        except Exception as e:
            print(f"Error getting account balance from Alpaca: {e}")
            return {}

    def get_latest_price(self, symbol: str) -> float:
        """Gets the latest market price for a symbol from Alpaca."""
        try:
            # Use the data_v2 client for market data (latest trade)
            trade = self.api.get_latest_trade(symbol)
            return trade.price
        except Exception as e:
            print(f"Error getting latest price for {symbol} from Alpaca: {e}")
            return 0.0  # Return 0 if price cannot be fetched

# --- Live Trader Engine ---
class LiveTrader:
    """
    The main engine for live trading. It integrates signals with a live adapter
    and applies risk management rules before execution.
    """
    def __init__(self, adapter: BaseLiveAdapter, risk_manager: RiskManager):
        """
        Initializes the LiveTrader.
        Args:
            adapter (BaseLiveAdapter): An instance of a concrete live trading adapter (e.g., AlpacaAdapter).
            risk_manager (RiskManager): An instance of the RiskManager for risk control.
        """
        self.adapter = adapter
        self.risk_manager = risk_manager
        self.trade_logger = get_logger("trade")  # Get the dedicated trade logger

    def process_signal(self, signal: Signal):
        """
        Processes a single trading signal. This is the main entry point for a signal
        to potentially trigger a live trade.
        """
        print(f"\n--- Processing Signal: {signal.signal_type} for {signal.symbol} at {signal.price} ---")
        
        # 1. Fetch current account status for risk checks
        account_info = self.adapter.get_account_balance()
        portfolio_value = float(account_info.get('equity', 0))
        cash_balance = float(account_info.get('cash', 0))

        # 2. Check system-wide circuit breakers
        if self.risk_manager.check_circuit_breakers(portfolio_value):
            print("Trading halted by circuit breaker. No order placed.")
            self.trade_logger.warning(
                "Trade skipped due to circuit breaker.",
                extra={"extra_data": asdict(signal)}
            )
            return
        
        # 3. Determine position size using RiskManager
        # For a real system, the stop_loss_price would be dynamically determined (e.g., from strategy, ATR)
        # For this example, we'll use a simplified dynamic stop-loss or use price directly
        stop_loss_price = signal.price * 0.98 if signal.signal_type == 'BUY' else signal.price * 1.02  # Example 2% SL
        
        quantity = self.risk_manager.calculate_position_size(
            symbol=signal.symbol,
            price=signal.price,
            stop_loss_price=stop_loss_price,
            portfolio_value=portfolio_value,
            cash_balance=cash_balance
        )
        
        # Ensure quantity is positive and meets minimum trade requirements (e.g., 1 share)
        if quantity < 1:  # Assuming integer shares for simplicity with Alpaca
            print(f"Calculated quantity ({quantity:.2f}) is too small or zero. Skipping trade.")
            self.trade_logger.info(
                "Trade skipped: calculated quantity too small.",
                extra={"extra_data": asdict(signal)}
            )
            return
        
        # 4. Place the order via the adapter
        order_confirmation = self.adapter.place_order(
            symbol=signal.symbol,
            order_type='market',  # We'll use market orders for simplicity
            quantity=quantity,
            side=signal.signal_type.lower()  # 'buy' or 'sell'
        )
        
        # 5. Log the live trade attempt and confirmation
        self.trade_logger.info(
            "Live trade order placed",
            extra={
                "extra_data": {
                    "signal": asdict(signal),
                    "order_confirmation": order_confirmation
                }
            }
        )
        print(f"Order placed. Confirmation: {order_confirmation.get('status', order_confirmation.get('error', 'UNKNOWN'))}")

# Example usage for direct execution and testing
if __name__ == "__main__":
    from utils.config_loader import config  # Import global config
    from datetime import datetime  # For signal timestamp

    print("--- Testing Live Integration Module ---")
    # 1. Initialize Risk Manager with example parameters (from config.yaml in a real app)
    try:
        risk_manager_params = config['risk_management']
    except KeyError:
        print("Error: 'risk_management' section missing in config.yaml. Using default params.")
        risk_manager_params = {
            'max_portfolio_risk_per_trade': 0.01,
            'max_position_exposure': 0.05,
            'daily_drawdown_limit': 0.05,
            'overall_drawdown_limit': 0.15
        }
    risk_manager = RiskManager(**risk_manager_params)

    # 2. Initialize Alpaca Adapter (requires API keys in .env and config.yaml)
    try:
        alpaca_adapter = AlpacaAdapter(
            api_key=config['api_keys']['alpaca_api_key'],
            api_secret=config['api_keys']['alpaca_api_secret'],
            paper=True  # IMPORTANT: Always start with paper trading for testing!
        )
        
        # 3. Initialize Live Trader with the adapter and risk manager
        live_trader = LiveTrader(adapter=alpaca_adapter, risk_manager=risk_manager)

        # 4. Create a mock signal and process it
        mock_symbol = 'AAPL'
        latest_price = alpaca_adapter.get_latest_price(mock_symbol)
        if latest_price > 0:
            print(f"\nFetched latest price for {mock_symbol}: ${latest_price:.2f}")
            mock_signal = Signal(
                timestamp=datetime.now(),
                symbol=mock_symbol,
                strategy='manual_live_test',  # Just a label for this test
                signal_type='BUY',
                price=latest_price  # Use the actual fetched price
            )
            
            live_trader.process_signal(mock_signal)
            
            # 5. Check account status and open positions after processing the signal
            print("\n--- Current Account Balance ---")
            print(alpaca_adapter.get_account_balance())
            
            print("\n--- Open Positions ---")
            open_positions = alpaca_adapter.get_open_positions()
            if open_positions:
                for pos in open_positions:
                    print(f"  {pos.get('symbol')}: {pos.get('qty')} shares, Avg Entry: ${pos.get('avg_entry_price')}, Current Value: ${pos.get('market_value')}")
            else:
                print("No open positions.")
            
            print("\n✅ Live Integration Module Test Completed.")
        else:
            print(f"Could not fetch latest price for {mock_symbol}. Cannot create mock signal. Skipping trade test.")

    except KeyError as e:
        print(f"\nERROR: Alpaca API keys not found in your config.yaml or .env file for key '{e}'.")
        print("Please ensure 'ALPACA_API_KEY' and 'ALPACA_API_SECRET' are set.")
        print("Skipping live integration test.")
    except Exception as e:
        print(f"\nAn unexpected error occurred during the live test: {e}")
