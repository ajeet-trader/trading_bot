import sys
from pathlib import Path
# Add project root to Python path for relative imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd
import pandas_ta as ta
import numpy as np
from typing import List

from data.data_storage import DataStorage

class FeatureEngineer:
    """
    A class to generate a rich set of features from processed market data.
    """
    def __init__(self, target_shift_periods: int = 5, target_threshold: float = 0.0):
        """
        Initializes the FeatureEngineer.

        Args:
            target_shift_periods (int): How many periods into the future to look for the target.
            target_threshold (float): The return threshold to classify as a '1' (up).
        """
        self.target_shift_periods = target_shift_periods
        self.target_threshold = target_threshold

    def generate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Main method to generate all features and the target variable.

        Args:
            df (pd.DataFrame): The input DataFrame with 'open', 'high', 'low', 'close', 'volume'.

        Returns:
            pd.DataFrame: The DataFrame enriched with features and a 'target' column.
        """
        # Ensure data is sorted by time
        df = df.sort_index()

        # 1. Generate Technical Indicators using pandas_ta
        df.ta.rsi(length=14, append=True)
        df.ta.macd(fast=12, slow=26, signal=9, append=True)
        df.ta.bbands(length=20, std=2, append=True)
        df.ta.atr(length=14, append=True)
        df.ta.adx(length=14, append=True)

        # 2. Generate Lagged Returns
        for lag in [1, 3, 5, 10, 21]:
            df[f'return_lag_{lag}'] = df['close'].pct_change(periods=lag)

        # 3. Generate Rolling Statistics
        for window in [5, 10, 20]:
            df[f'rolling_mean_{window}'] = df['close'].rolling(window=window).mean()
            df[f'rolling_std_{window}'] = df['close'].rolling(window=window).std()
            df[f'rolling_vol_mean_{window}'] = df['volume'].rolling(window=window).mean()

        # 4. Generate Time-Based Features
        df['day_of_week'] = df.index.dayofweek
        df['month_of_year'] = df.index.month

        # 5. Create the Target Variable
        # The target is the future return, shifted back to the current row.
        future_returns = df['close'].pct_change(self.target_shift_periods).shift(-self.target_shift_periods)
        df['target'] = (future_returns > self.target_threshold).astype(int)

        # Clean up the DataFrame
        # Drop rows with NaN values created by indicators and lags
        df = df.dropna()

        return df

# Example usage for direct execution and testing
if __name__ == "__main__":
    print("--- Running Feature Engineering ---")
    
    # 1. Setup
    symbol = 'AAPL'
    interval = '1d'
    storage = DataStorage()
    
    # 2. Load processed data
    print(f"Loading processed data for {symbol}...")
    processed_data = storage.load_data(symbol, interval)
    assert not processed_data.empty, f"No processed data found for {symbol}. Please run the data pipeline first."
    
    # 3. Engineer features
    print("Generating features...")
    feature_engineer = FeatureEngineer()
    feature_df = feature_engineer.generate_features(processed_data)
    
    # 4. Inspect the results
    print("\nFeature-engineered DataFrame (first 5 rows):")
    print(feature_df.head())
    
    print("\nFeature-engineered DataFrame (last 5 rows):")
    print(feature_df.tail())
    
    print(f"\nTotal features created: {len(feature_df.columns)}")
    print(f"Target distribution:\n{feature_df['target'].value_counts(normalize=True)}")
    
    # 5. Save the feature data
    # This activates the `data/features/` directory
    features_path = Path(__file__).parent.parent / "data" / "features"
    features_path.mkdir(exist_ok=True)
    safe_symbol = symbol.replace('/', '_')
    features_file = features_path / f"{safe_symbol}_{interval}_features.parquet"
    feature_df.to_parquet(features_file)
    
    print(f"\n✅ Successfully generated and saved feature data to: {features_file}")