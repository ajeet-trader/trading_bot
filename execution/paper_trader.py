import sys
from pathlib import Path

# Add project root to Python path for relative imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from typing import List, Dict, Tuple
from utils.data_structures import Signal # Import our Signal dataclass
from utils.logger_setup import get_logger # Import our logging utility
class PaperTrader:
    """
    Simulates trade execution and manages a virtual portfolio.
    It processes trading signals, applies transaction costs (commission, slippage),
    and logs simulated trades.
    """
    def __init__(self, 
                 initial_capital: float, 
                 commission: float, 
                 slippage: float, 
                 risk_per_trade: float):
        """
        Initializes the PaperTrader with starting capital and cost parameters.
        Args:
            initial_capital (float): The starting amount of cash for the simulation.
            commission (float): The fixed commission cost per trade.
            slippage (float): The percentage of price slippage to apply (e.g., 0.001 for 0.1%).
            risk_per_trade (float): The fraction of available cash to risk per BUY trade for position sizing.
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.risk_per_trade = risk_per_trade
        # Portfolio: {'SYMBOL': {'size': float, 'entry_price': float}}
        self.portfolio: Dict[str, Dict] = {}
        self.trade_logger = get_logger("trade") # Get the dedicated trade logger
    def _execute_trade(self, 
                       signal: Signal, 
                       current_price: float) -> Tuple[float, float, float]:
        """
        Simulates the execution of a single trade, returning changes to cash and position.
        Args:
            signal (Signal): The trading signal to execute (BUY/SELL).
            current_price (float): The current market price at which the signal was generated.
        Returns:
            Tuple[float, float, float]: 
                - The change in cash balance.
                - The change in position size for the symbol.
                - The actual execution price after accounting for slippage.
        """
        # 1. Calculate execution price with slippage
        if signal.signal_type == 'BUY':
            execution_price = current_price * (1 + self.slippage)
        elif signal.signal_type == 'SELL':
            execution_price = current_price * (1 - self.slippage)
        else:
            return 0.0, 0.0, current_price # No changes for 'HOLD' signals
        # 2. Determine trade size and calculate changes
        position_for_symbol = self.portfolio.get(signal.symbol, {'size': 0})
        cash_change = 0.0
        position_change = 0.0
        if signal.signal_type == 'BUY':
            # Fixed fractional position sizing based on risk_per_trade
            trade_value = self.cash * self.risk_per_trade
            quantity = trade_value / execution_price
            
            # Ensure we have enough cash for the trade plus commission
            if self.cash >= (quantity * execution_price) + self.commission:
                cash_change = - (quantity * execution_price) - self.commission
                position_change = quantity
            else:
                self.trade_logger.warning(f"Insufficient cash for BUY signal for {signal.symbol}. Skipping.")
                return 0.0, 0.0, execution_price # Trade not executed
        
        elif signal.signal_type == 'SELL':
            # If there's an open position, sell the entire quantity
            if position_for_symbol['size'] > 0:
                quantity = position_for_symbol['size']
                cash_change = (quantity * execution_price) - self.commission
                position_change = -quantity
            else:
                self.trade_logger.warning(f"No open position for {signal.symbol} to SELL. Skipping.")
                return 0.0, 0.0, execution_price # No position to sell
        return cash_change, position_change, execution_price
    def run(self, signals: List[Signal]):
        """
        Runs the paper trading simulation by processing a list of signals.
        """
        print("--- Starting Paper Trading Simulation ---")
        
        for signal in signals:
            # In a real live trading system, `current_price` would be fetched from a live data feed.
            # For this paper trading simulation, we use the `price` from the `Signal` object.
            current_price = signal.price
            
            cash_delta, position_delta, exec_price = self._execute_trade(signal, current_price)
            
            # Only update portfolio and log if a trade actually occurred
            if position_delta != 0.0:
                self.cash += cash_delta
                
                # Update the specific position in the portfolio
                current_position = self.portfolio.get(signal.symbol, {'size': 0, 'entry_price': 0})
                new_size = current_position['size'] + position_delta
                
                if new_size > 1e-6: # Position still open or increased
                    # Calculate new average entry price if adding to position
                    if current_position['size'] > 0 and position_delta > 0:
                        total_value = (current_position['size'] * current_position['entry_price']) + (position_delta * exec_price)
                        new_entry_price = total_value / new_size
                    else: # New position or fully reversed position
                        new_entry_price = exec_price
                    
                    self.portfolio[signal.symbol] = {
                        'size': new_size,
                        'entry_price': new_entry_price
                    }
                else: # Position closed (or became negligibly small)
                    if signal.symbol in self.portfolio:
                        del self.portfolio[signal.symbol]
                # Log the trade details to the structured trade log
                self.trade_logger.info("Paper trade executed", extra={
                    "extra_data": {
                        "timestamp": signal.timestamp.isoformat(),
                        "symbol": signal.symbol,
                        "action": signal.signal_type,
                        "quantity": abs(position_delta),
                        "price": exec_price,
                        "cash_change": cash_delta,
                        "current_cash": self.cash
                    }
                })
                self.print_status() # Print status after each trade for clarity
    def print_status(self):
        """Prints the current status of the paper trading portfolio to the console."""
        print(f"\n--- Portfolio Status ---")
        print(f"Cash: ${self.cash:,.2f}") # Format cash to 2 decimal places with commas
        
        total_position_value = 0.0
        if not self.portfolio:
            print("Positions: None")
        else:
            print("Positions:")
            for symbol, pos in self.portfolio.items():
                # For status, just use the entry price to estimate market value,
                # In a real-time system, this would fetch current market prices.
                market_value = pos['size'] * pos['entry_price'] 
                total_position_value += market_value
                print(f"  - {symbol}: Size={pos['size']:.4f}, Entry=${pos['entry_price']:.2f}, Market Value=${market_value:,.2f}")
        
        total_equity = self.cash + total_position_value
        print(f"Total Equity: ${total_equity:,.2f}")
# Example usage for direct execution and testing
if __name__ == "__main__":
    from datetime import datetime, timedelta
    
    # 1. Initialize the paper trader with example parameters
    paper_trader = PaperTrader(
        initial_capital=100_000.0, # Start with 100,000 virtual dollars
        commission=1.0,            # $1 commission per trade
        slippage=0.001,            # 0.1% slippage on price
        risk_per_trade=0.05        # Risk 5% of cash per BUY trade
    )
    paper_trader.print_status() # Show initial empty portfolio
    # 2. Create a stream of mock signals to simulate
    now = datetime.now()
    mock_signals = [
        # BUY AAPL (initial position)
        Signal(timestamp=now, symbol='AAPL', strategy='test_strategy', signal_type='BUY', price=150.0),
        # BUY MSFT (new position)
        Signal(timestamp=now + timedelta(days=1), symbol='MSFT', strategy='test_strategy', signal_type='BUY', price=300.0),
        # SELL AAPL (close position)
        Signal(timestamp=now + timedelta(days=2), symbol='AAPL', strategy='test_strategy', signal_type='SELL', price=155.0),
        # BUY GOOG (new position)
        Signal(timestamp=now + timedelta(days=3), symbol='GOOG', strategy='test_strategy', signal_type='BUY', price=2800.0),
        # SELL MSFT (close position)
        Signal(timestamp=now + timedelta(days=4), symbol='MSFT', strategy='test_strategy', signal_type='SELL', price=295.0),
    ]
    # 3. Run the simulation by feeding the signals to the paper trader
    paper_trader.run(mock_signals)
    
    print("\n--- Final Portfolio Status ---")
    paper_trader.print_status() # Show final portfolio state