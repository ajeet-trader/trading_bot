from abc import ABC, abstractmethod
from datetime import datetime
from typing import List
import pandas as pd
class BaseAPIAdapter(ABC):
    """
    Abstract Base Class for all data API adapters.
    Defines the common interface for fetching market data.
    """
    def __init__(self, name: str):
        self.name = name
    @abstractmethod
    def fetch_historical_data(self, 
                              symbol: str, 
                              start_date: datetime, 
                              end_date: datetime, 
                              interval: str = '1d') -> pd.DataFrame:
        """
        Fetches historical OHLCV data for a given symbol and time range.
        Args:
            symbol (str): The trading symbol (e.g., 'AAPL', 'BTC/USDT').
            start_date (datetime): The start date for the historical data.
            end_date (datetime): The end date for the historical data.
            interval (str): The data interval (e.g., '1d', '1h', '5m').
        Returns:
            pd.DataFrame: A DataFrame with columns:
                          'timestamp', 'open', 'high', 'low', 'close', 'volume'.
                          Returns an empty DataFrame if no data is found or on error.
        """
        pass
    @abstractmethod
    def fetch_realtime_data(self, symbol: str) -> pd.DataFrame:
        """
        Fetches the latest real-time OHLCV data (e.g., current bar or latest tick).
        The exact behavior depends on the API.
        Args:
            symbol (str): The trading symbol.
        Returns:
            pd.DataFrame: A DataFrame with the latest data, or empty if not available.
        """
        pass
    @abstractmethod
    def get_available_symbols(self) -> List[str]:
        """
        Fetches a list of symbols available through this adapter.
        Returns:
            List[str]: A list of available trading symbols.
        """
        pass
    def _standardize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Helper method to standardize DataFrame column names.
        Subclasses should call this after fetching data.
        """
        # Convert column names to lowercase for consistency
        df.columns = [col.lower() for col in df.columns]
        # Rename common variations to our standard names
        column_mapping = {
            'date': 'timestamp',
            'datetime': 'timestamp',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'adj close': 'adj_close', # For Yahoo Finance adjusted close
            'volume': 'volume'
        }
        df = df.rename(columns=column_mapping)
        # Ensure 'timestamp' is datetime and set as index if not already
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
            df = df.set_index('timestamp')
        elif isinstance(df.index, pd.DatetimeIndex):
            df.index.name = 'timestamp'
            df.index = df.index.tz_localize(None).tz_localize('UTC') # Ensure UTC and no timezone
        else:
            raise ValueError("DataFrame must have a 'timestamp' column or a DatetimeIndex.")
        # Select and reorder standard columns
        standard_cols = ['open', 'high', 'low', 'close', 'volume']
        # Filter for columns that actually exist in the DataFrame
        existing_standard_cols = [col for col in standard_cols if col in df.columns]
        
        return df[existing_standard_cols]