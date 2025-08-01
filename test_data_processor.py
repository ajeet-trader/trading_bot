import pandas as pd
import numpy as np
from datetime import datetime
from data.data_processor import DataProcessor

def create_test_data() -> pd.DataFrame:
    """Creates a DataFrame with various data quality issues."""
    dates = pd.to_datetime([datetime(2023, 1, i) for i in range(1, 11)], utc=True)
    data = {
        'open':   [150, 151, 152, np.nan, 154, 155, 156, 157, 158, 159],
        'high':   [152, 153, 154, 155, 153, 157, 158, 159, 160, 161],  # 2023-01-05 has high < low
        'low':    [149, 150, 151, 152, 154, 154, 156, 157, 158, 159],
        'close':  [151, 152, 153, 154, 155, 156, 157, 158, 159, 160],
        'volume': [1000, 1200, 800, 900, 1000, 50000, -50, 1300, 1400, 1500]  # Volume outlier and negative
    }
    df = pd.DataFrame(data, index=dates)
    df.index.name = 'timestamp'
    return df

if __name__ == "__main__":
    print("--- Testing Data Processor ---")
    processor = DataProcessor()

    test_df = create_test_data()
    print("\nOriginal Test Data:")
    print(test_df)

    processed_df, metrics = processor.process_data(test_df.copy(), "TEST_SYMBOL")

    print("\nProcessed Data:")
    print(processed_df)

    print("\nQuality Metrics:")
    print(metrics)

    # --- Validation Checks ---
    print("\n--- Validation Results ---")
    assert metrics['initial_rows'] == 10, "Initial row count is wrong"
    assert metrics['missing_values_filled'] > 0, "Failed to fill missing values"
    assert metrics['invalid_rows_removed'] == 2, "Expected 2 invalid rows removed (NegVol and High<Low)"
    assert metrics['outliers_corrected'] == 0, "Expected 0 outliers corrected"
    assert (processed_df['volume'] >= 0).all(), "Negative volume not removed"
    assert (processed_df['high'] >= processed_df['low']).all(), "Invalid H<L rows not handled"
    print("All validation checks passed successfully!")
