from datetime import datetime, timedelta

import pandas as pd
from data.api_adapters.yahoo_finance_adapter import YahooFinanceAdapter
from data.data_processor import DataProcessor
from data.data_storage import DataStorage

if __name__ == "__main__":
    print("--- Testing Full Data Pipeline (Fetch -> Process -> Store -> Load) ---")
    
    # 1. Setup
    symbol = 'AAPL'
    interval = '1d'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5 * 365)
    #end_date = datetime(2025, 7, 30)
    #start_date = datetime(2020, 1, 1)
    
    adapter = YahooFinanceAdapter()
    processor = DataProcessor()
    storage = DataStorage()
    
    # 2. Fetch raw data
    print(f"\n[Step 1] Fetching raw data for {symbol}...")
    raw_df = adapter.fetch_historical_data(symbol, start_date, end_date, interval)
    assert not raw_df.empty, "Failed to fetch raw data."
    print(f"Fetched {len(raw_df)} raw rows.")
    
    # 3. Process the data
    print("\n[Step 2] Processing data...")
    processed_df, metrics = processor.process_data(raw_df, symbol)
    assert not processed_df.empty, "Processing resulted in an empty DataFrame."
    print(f"Processed data, final rows: {metrics['final_rows']}. Metrics: {metrics}")
    
    # 🧠 Enforce datetime index with UTC timezone
    processed_df.index = pd.to_datetime(processed_df.index, utc=True)
    processed_df.index.name = "timestamp"
    
    # 4. Save the processed data
    print("\n[Step 3] Saving processed data...")
    storage.save_data(processed_df, symbol, interval)
    
    # 5. Load the data back from storage
    print("\n[Step 4] Loading data from storage...")
    loaded_df = storage.load_data(symbol, interval)
    assert not loaded_df.empty, "Failed to load data from storage."
    
    # 6. Verify integrity
    print("\n[Step 5] Verifying data integrity...")
    pd.testing.assert_frame_equal(processed_df, loaded_df)
    print("✅ Data integrity check passed! The saved and loaded data are identical.")
    
    print("\n--- Full Data Pipeline Test Successful! ---")