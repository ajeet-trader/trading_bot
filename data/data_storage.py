import pandas as pd
from pathlib import Path
from typing import Optional
from datetime import datetime
from utils.logger_setup import get_logger

# Initialize a logger for error and info messages in this module
logger = get_logger("error")

class DataStorage:
    """
    Handles saving and loading of processed market data as Parquet files.
    Ensures datetime indices are UTC-aware for consistent filtering.
    """

    def __init__(self, base_path: str = 'data/processed'):
        """
        Initialize storage location root.

        Args:
            base_path: Folder where processed data will be saved/loaded.
        """
        # Create base_path relative to the project root directory
        self.base_path = Path(__file__).parent.parent / base_path
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"DataStorage initialized. Storage path: {self.base_path}")

    def _get_file_path(self, symbol: str, interval: str) -> Path:
        """
        Create a standard file path for a given symbol and interval.

        Args:
            symbol: trading instrument symbol, e.g., 'AAPL' or 'BTC/USDT'
            interval: data frequency, e.g., '1d', '1h'

        Returns:
            pathlib.Path for the Parquet file storage location.
        """
        # Replace any path-unfriendly chars (e.g., '/')
        safe_symbol = symbol.replace('/', '_').replace('\\', '_')

        # Folder per interval (e.g., data/processed/1d)
        interval_path = self.base_path / interval
        interval_path.mkdir(exist_ok=True)
        return interval_path / f"{safe_symbol}.parquet"

    def save_data(self, df: pd.DataFrame, symbol: str, interval: str):
        """
        Save a DataFrame of processed data as a compressed Parquet file.

        Args:
            df: DataFrame with datetime index and OHLCV columns.
            symbol: Trading instrument symbol.
            interval: Data frequency.
        """
        if df.empty:
            logger.warning(f"Attempted to save empty DataFrame for {symbol} at {interval}. Skipping.")
            return

        file_path = self._get_file_path(symbol, interval)
        try:
            # Save using efficient Parquet format with Snappy compression
            df.to_parquet(file_path, engine='pyarrow', compression='snappy')
            logger.info(f"Successfully saved {len(df)} rows for {symbol} ({interval}) to {file_path}")
        except Exception as e:
            logger.exception(f"Failed to save data for {symbol} to {file_path}: {e}")

    def load_data(self,
                  symbol: str,
                  interval: str,
                  start_date: Optional[datetime] = None,
                  end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Load stored data optionally sliced between start_date and end_date.

        Args:
            symbol: Trading instrument symbol.
            interval: Data frequency.
            start_date: Start of date filter (inclusive).
            end_date: End of date filter (inclusive).

        Returns:
            DataFrame with filtered data or empty if file missing/error.
        """
        file_path = self._get_file_path(symbol, interval)
        if not file_path.exists():
            logger.warning(f"Data file not found for {symbol} ({interval}) at {file_path}")
            return pd.DataFrame()

        try:
            # Read Parquet file into DataFrame
            df = pd.read_parquet(file_path, engine='pyarrow')

            # Make sure index is datetime and timezone aware (UTC)
            df.index = pd.to_datetime(df.index, utc=True)

            # Ensure start_date and end_date are also timezone-aware before filtering
            if start_date:
                if getattr(start_date, 'tzinfo', None) is None:
                    start_date = pd.Timestamp(start_date).tz_localize("UTC")
                df = df[df.index >= start_date]

            if end_date:
                if getattr(end_date, 'tzinfo', None) is None:
                    end_date = pd.Timestamp(end_date).tz_localize("UTC")
                df = df[df.index <= end_date]

            logger.info(f"Returning {len(df)} rows after date slicing for {symbol} at {interval}.")
            print(f"[DataStorage] Loaded {len(df)} rows for {symbol} between {start_date} and {end_date} from {file_path}")
            return df

        except Exception as e:
            logger.exception(f"Failed to load data for {symbol} from {file_path}: {e}")
            return pd.DataFrame()


if __name__ == "__main__":
    # Basic test when run independently
    from datetime import timedelta

    print("--- Testing DataStorage ---")
    storage = DataStorage()

    # Create a sample dataframe for testing with hourly data for ~4 days
    symbol = 'TEST/SYM'
    interval = '1h'
    end_time = pd.Timestamp.now(tz="UTC").replace(minute=0, second=0, microsecond=0)
    start_time = end_time - timedelta(hours=100)
    dates = pd.date_range(start=start_time, end=end_time, freq='H', tz="UTC")

    sample_df = pd.DataFrame({
        'open': range(len(dates)),
        'high': range(len(dates)),
        'low': range(len(dates)),
        'close': range(len(dates)),
        'volume': range(len(dates))
    }, index=dates)
    sample_df.index.name = 'timestamp'

    storage.save_data(sample_df, symbol, interval)
    loaded_df = storage.load_data(symbol, interval)
    assert len(loaded_df) == len(sample_df)
    assert loaded_df.index.equals(sample_df.index)
    pd.testing.assert_frame_equal(sample_df, loaded_df)
    print("✅ Test passed.")
