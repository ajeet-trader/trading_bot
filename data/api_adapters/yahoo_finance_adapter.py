import yfinance as yf
import pandas as pd
from datetime import datetime, timezone  
from typing import List
from data.api_adapters.base_adapter import BaseAPIAdapter
from utils.logger_setup import get_logger
logger = get_logger("error") # Use the error logger for issues
class YahooFinanceAdapter(BaseAPIAdapter):
    """
    Data adapter for Yahoo Finance using the yfinance library.
    Primarily for historical stock data.
    """
    def __init__(self):
        super().__init__("Yahoo Finance")
        self.symbols_cache = {} # Simple cache for available symbols
    def fetch_historical_data(self, 
                              symbol: str, 
                              start_date: datetime, 
                              end_date: datetime, 
                              interval: str = '1d') -> pd.DataFrame:
        """
        Fetches historical OHLCV data from Yahoo Finance.
        Args:
            symbol (str): The stock ticker symbol (e.g., 'AAPL', 'MSFT').
            start_date (datetime): The start date.
            end_date (datetime): The end date.
            interval (str): Data interval (e.g., '1d', '1wk', '1mo').
                            Note: yfinance has limited intraday intervals for long periods.
        Returns:
            pd.DataFrame: Standardized DataFrame or empty DataFrame on error/no data.
        """
        try:
            # yfinance expects dates as strings or datetime objects
            # It handles timezone conversion internally, but we'll standardize to UTC later
            df = yf.download(symbol, start=start_date, end=end_date, interval=interval, progress=False, auto_adjust=False)
            #print(f"Raw Yahoo Finance data for {symbol}:\n{df.head()}")
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)


            
            if df.empty:
                logger.warning(f"No historical data found for {symbol} from {self.name} for {start_date} to {end_date}")
                return pd.DataFrame()
            
            # Standardize column names and index
            df = self._standardize_dataframe(df)
            return df
        except Exception as e:
            logger.error(f"Error fetching historical data from {self.name} for {symbol}: {e}")
            return pd.DataFrame()
    def fetch_realtime_data(self, symbol: str) -> pd.DataFrame:
        """
        Fetches the latest real-time data (current price) from Yahoo Finance.
        Note: yfinance's real-time capabilities are limited to current price/info.
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info:
                logger.warning(f"No real-time info found for {symbol} from {self.name}")
                return pd.DataFrame()
            # Construct a DataFrame for consistency
            current_time = datetime.now().astimezone(datetime.now().astimezone().tzinfo) # Local timezone
            current_time_utc = current_time.astimezone(timezone.utc) # Convert to UTC
            
            data = {
                'timestamp': [current_time_utc],
                'open': [info.get('open')],
                'high': [info.get('dayHigh')],
                'low': [info.get('dayLow')],
                'close': [info.get('currentPrice')],
                'volume': [info.get('volume')]
            }
            df = pd.DataFrame(data).set_index('timestamp')
            df = self._standardize_dataframe(df)
            return df
        except Exception as e:
            logger.error(f"Error fetching real-time data from {self.name} for {symbol}: {e}")
            return pd.DataFrame()
    def get_available_symbols(self) -> List[str]:
        """
        Yahoo Finance doesn't provide a direct API for all available symbols.
        This method would typically be populated from a predefined list or a database.
        For now, we return a small hardcoded list for demonstration.
        In a real system, this would involve a much larger, dynamic list.
        """
        if not self.symbols_cache:
            # In a real system, you'd fetch this from a reliable source or a local database
            self.symbols_cache = [
                'AAPL', 'MSFT', 'GOOG', 'AMZN', 'TSLA', 'NVDA', 'JPM', 'V', 'PG', 'JNJ'
            ]
            logger.info(f"Loaded {len(self.symbols_cache)} demo symbols for {self.name}.")
        return self.symbols_cache