import sys
from pathlib import Path

# Add project root to Python path for relative imports
sys.path.append(str(Path(__file__).resolve().parent.parent))


from typing import Dict, Optional
from utils.logger_setup import get_logger # Import our logging utility
class RiskManager:
    """
    Manages position sizing and portfolio-level risk controls for a trading system.
    Includes logic for calculating trade size based on risk and implementing circuit breakers.
    """
    def __init__(self, 
                 max_portfolio_risk_per_trade: float,
                 max_position_exposure: float,
                 daily_drawdown_limit: float,
                 overall_drawdown_limit: float):
        """
        Initializes the RiskManager with defined limits and thresholds.
        Args:
            max_portfolio_risk_per_trade (float): Max percentage of total portfolio value to risk per trade (e.g., 0.01 for 1%).
            max_position_exposure (float): Max percentage of total portfolio value allowed in a single position (e.g., 0.10 for 10%).
            daily_drawdown_limit (float): Max percentage of drawdown from daily high before halting trading (e.g., 0.05 for 5%).
            overall_drawdown_limit (float): Max percentage of drawdown from all-time high before halting trading (e.g., 0.15 for 15%).
        """
        self.max_portfolio_risk_per_trade = max_portfolio_risk_per_trade
        self.max_position_exposure = max_position_exposure
        self.daily_drawdown_limit = daily_drawdown_limit
        self.overall_drawdown_limit = overall_drawdown_limit
        
        self.daily_high_value: Optional[float] = None # Tracks the highest value reached today
        self.overall_high_value: Optional[float] = None # Tracks the all-time highest value reached
        
        self.logger = get_logger("error") # Use the error logger for critical events
    def calculate_position_size(self, 
                                symbol: str, 
                                price: float, 
                                stop_loss_price: float, 
                                portfolio_value: float, 
                                cash_balance: float) -> float:
        """
        Calculates the appropriate position size (quantity of units) for a new trade
        based on defined risk parameters.
        Args:
            symbol (str): The trading symbol.
            price (float): The current market price of the asset.
            stop_loss_price (float): The price level at which the trade would be exited for a loss.
                                     Must be different from 'price'.
            portfolio_value (float): The current total value of the trading portfolio (cash + open positions).
            cash_balance (float): The current available cash.
        Returns:
            float: The calculated number of shares/units to trade. Returns 0 if trade is not viable.
        """
        # 1. Determine the total dollar amount to risk on this specific trade
        dollar_risk_per_trade = portfolio_value * self.max_portfolio_risk_per_trade
        
        # 2. Determine the risk per share based on the stop-loss distance
        risk_per_share = abs(price - stop_loss_price)
        if risk_per_share <= 1e-6: # Avoid division by zero or near-zero risk (e.g., stop loss == entry price)
            self.logger.warning(f"Risk per share for {symbol} is too small or zero ({risk_per_share}). Cannot calculate position size meaningfully.")
            return 0.0
        
        # 3. Calculate the initial position size based on dollar risk and risk per share
        calculated_quantity = dollar_risk_per_trade / risk_per_share
        
        # 4. Enforce constraints: cash availability and maximum single position exposure
        # Convert quantity to its equivalent dollar value for checks
        trade_value = calculated_quantity * price
        # Adjust quantity based on available cash (cannot exceed cash balance)
        if trade_value > cash_balance:
            self.logger.warning(f"Downsizing trade for {symbol}: calculated value ${trade_value:,.2f} exceeds cash ${cash_balance:,.2f}. Adjusting to cash limit.")
            calculated_quantity = (cash_balance / price) * 0.99 # Leave a small buffer
            trade_value = calculated_quantity * price # Recalculate trade value
        # Adjust quantity based on maximum single position exposure
        max_allowed_position_value = portfolio_value * self.max_position_exposure
        if trade_value > max_allowed_position_value:
            self.logger.warning(f"Downsizing trade for {symbol}: value ${trade_value:,.2f} exceeds max exposure ${max_allowed_position_value:,.2f}. Adjusting to exposure limit.")
            calculated_quantity = max_allowed_position_value / price
            
        # Ensure quantity is not negative or zero due to calculations
        if calculated_quantity < 1e-6:
            self.logger.warning(f"Calculated quantity for {symbol} is too small ({calculated_quantity}). Returning 0.")
            return 0.0
        return calculated_quantity
    def check_circuit_breakers(self, portfolio_value: float) -> bool:
        """
        Checks if any system-level circuit breakers have been tripped based on portfolio value.
        Updates high-water marks and triggers critical alerts if limits are exceeded.
        Args:
            portfolio_value (float): The current total equity of the portfolio.
        Returns:
            bool: True if trading should be halted (a circuit breaker is tripped), False otherwise.
        """
        # Initialize high-water marks if they are None (first check or after reset)
        if self.daily_high_value is None: 
            self.daily_high_value = portfolio_value
        if self.overall_high_value is None: 
            self.overall_high_value = portfolio_value
        # Update high-water marks (always track the highest value achieved)
        self.daily_high_value = max(self.daily_high_value, portfolio_value)
        self.overall_high_value = max(self.overall_high_value, portfolio_value)
        
        # Check daily drawdown limit
        daily_drawdown = (self.daily_high_value - portfolio_value) / self.daily_high_value
        if daily_drawdown > self.daily_drawdown_limit:
            self.logger.critical(f"CIRCUIT BREAKER TRIPPED (DAILY): Portfolio drawdown of {daily_drawdown:.2%} (from daily high ${self.daily_high_value:,.2f}) exceeded limit of {self.daily_drawdown_limit:.2%}. Halting trading.")
            return True # Halt trading
            
        # Check overall drawdown limit
        overall_drawdown = (self.overall_high_value - portfolio_value) / self.overall_high_value
        if overall_drawdown > self.overall_drawdown_limit:
            self.logger.critical(f"CIRCUIT BREAKER TRIPPED (OVERALL): Portfolio drawdown of {overall_drawdown:.2%} (from all-time high ${self.overall_high_value:,.2f}) exceeded limit of {self.overall_drawdown_limit:.2%}. Halting trading.")
            return True # Halt trading
            
        return False # No circuit breakers tripped
    def reset_daily_limits(self):
        """
        Resets the daily tracking variables (daily_high_value) to None.
        This should be called at the start of each new trading day.
        """
        self.daily_high_value = None
        self.logger.info("Daily risk limits have been reset.")
# Example usage for direct execution and testing of the RiskManager
if __name__ == "__main__":
    print("--- Testing RiskManager ---")
    # 1. Initialize the RiskManager with example limits
    risk_manager = RiskManager(
        max_portfolio_risk_per_trade=0.02, # Risk 2% of total portfolio value per trade
        max_position_exposure=0.10,      # Max 10% of total portfolio value in any single position
        daily_drawdown_limit=0.05,       # Halt if portfolio drops 5% from daily high
        overall_drawdown_limit=0.15      # Halt if portfolio drops 15% from all-time high
    )
    
    # --- Test Case 1: Position Sizing ---
    print("\n--- Position Sizing Test ---")
    initial_portfolio_value = 100_000.0
    initial_cash_balance = 100_000.0
    # Scenario A: Standard calculation
    # Risk $2000 (2% of 100k). If risk/share is $5 (150-145), then 2000/5 = 400 shares.
    calculated_quantity_a = risk_manager.calculate_position_size(
        symbol='AAPL',
        price=150.0,
        stop_loss_price=145.0, # $5 risk per share
        portfolio_value=initial_portfolio_value,
        cash_balance=initial_cash_balance
    )
    print(f"Scenario A (Standard): Calculated Quantity: {calculated_quantity_a:.2f} shares")
    print(f"  Trade Value: ${calculated_quantity_a * 150.0:,.2f}")
    assert abs(calculated_quantity_a - 400) < 0.01, "Position size calculation (Scenario A) is incorrect."
    print("✅ Scenario A: Position sizing calculation is correct.")
    # Scenario B: Constrained by cash (e.g., only $5000 cash left)
    # Calculated 400 shares * $150 = $60,000. If only $5000 cash, it should be limited.
    calculated_quantity_b = risk_manager.calculate_position_size(
        symbol='MSFT',
        price=300.0,
        stop_loss_price=290.0, # $10 risk per share
        portfolio_value=initial_portfolio_value, # still 100k total value
        cash_balance=5000.0 # Only 5k cash left
    )
    print(f"Scenario B (Cash Constrained): Calculated Quantity: {calculated_quantity_b:.2f} shares")
    print(f"  Trade Value: ${calculated_quantity_b * 300.0:,.2f}")
    assert calculated_quantity_b * 300.0 <= 5000.0, "Position size (Scenario B) not constrained by cash."
    print("✅ Scenario B: Position sizing constrained by cash correctly.")
    # Scenario C: Constrained by max exposure (10% of 100k = $10,000 max position value)
    calculated_quantity_c = risk_manager.calculate_position_size(
        symbol='GOOG',
        price=2000.0,
        stop_loss_price=1900.0, # $100 risk per share
        portfolio_value=initial_portfolio_value,
        cash_balance=100_000.0 # Plenty of cash
    )
    print(f"Scenario C (Exposure Constrained): Calculated Quantity: {calculated_quantity_c:.2f} shares")
    print(f"  Trade Value: ${calculated_quantity_c * 2000.0:,.2f}")
    assert calculated_quantity_c * 2000.0 <= 10000.0, "Position size (Scenario C) not constrained by max exposure."
    print("✅ Scenario C: Position sizing constrained by max exposure correctly.")
    
    # --- Test Case 2: Circuit Breakers ---
    print("\n--- Circuit Breaker Test ---")
    
    # Simulate a series of portfolio value changes to trip daily drawdown
    # Initial value: 100k, Peak: 101k, Drop to 94k is (101k - 94k)/101k = ~6.9% drawdown, >5% limit
    portfolio_values_daily = [100000, 101000, 98000, 96000, 94000] 
    halt_trading_daily = False
    for value in portfolio_values_daily:
        if not halt_trading_daily:
            print(f"  Current Portfolio Value: ${value:,.2f}")
            halt_trading_daily = risk_manager.check_circuit_breakers(value)
        else:
            print(f"  Trading is HALTED (at value ${value:,.2f}).")
            break
    
    assert halt_trading_daily, "Daily drawdown circuit breaker did not trip as expected."
    print("✅ Daily drawdown circuit breaker tripped correctly.")
    
    # Reset daily limits for next test
    risk_manager.reset_daily_limits()
    
    # Simulate an overall drawdown (e.g., from an all-time high of 120k to current 100k)
    # (120k - 100k) / 120k = ~16.67% drawdown, >15% limit
    risk_manager.overall_high_value = 120000.0 # Manually set a higher overall peak
    current_value_overall = 100000.0
    print(f"  Current Portfolio Value (for overall test): ${current_value_overall:,.2f}")
    halt_trading_overall = risk_manager.check_circuit_breakers(current_value_overall)
    
    assert halt_trading_overall, "Overall drawdown circuit breaker did not trip as expected."
    print("✅ Overall drawdown circuit breaker tripped correctly.")
    print("\n--- RiskManager Tests Complete ---")