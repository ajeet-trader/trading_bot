#YAHOO FINANCE ADAPTER TEST SCRIPT
# This script tests the Yahoo Finance Adapter for fetching historical and real-time data.

from data.api_adapters.yahoo_finance_adapter import YahooFinanceAdapter
from datetime import datetime, timedelta
print("\n--- Testing Yahoo Finance Adapter (Historical) ---")
yf_adapter = YahooFinanceAdapter()

end_date = datetime.now()
start_date = end_date - timedelta(days=30) # Last 30 days

# Test valid symbol
df_aapl = yf_adapter.fetch_historical_data('AAPL', start_date, end_date, '1d')
if not df_aapl.empty:
    print(f"AAPL Historical Data (last 5 rows):\n{df_aapl.tail()}")
    print(f"AAPL Data Columns: {df_aapl.columns.tolist()}")
    print(f"AAPL Data Index Type: {type(df_aapl.index)}")
else:
    print("Failed to fetch AAPL historical data.")

# Test INvalid symbol
df_invalid = yf_adapter.fetch_historical_data('INVALID_SYMBOL', start_date, end_date, '1d')
if df_invalid.empty:
    print("Successfully handled invalid symbol for Yahoo Finance (returned empty DataFrame).")

print("\n--- Testing Yahoo Finance Adapter (Real-time) ---")
df_aapl_rt = yf_adapter.fetch_realtime_data('AAPL')
if not df_aapl_rt.empty:
    print(f"AAPL Real-time Data:\n{df_aapl_rt}")
else:
    print("Failed to fetch AAPL real-time data.")


"""
import yfinance as yf
from datetime import datetime, timedelta

end_date = datetime.now()
start_date = end_date - timedelta(days=30)
print(f"{start_date=}, {end_date=}")
df = yf.download('AAPL', start=start_date, end=end_date, interval='1d', progress=False)
print(df.head())
"""
# BINANCE ADAPTER TEST SCRIPT
# This script tests the Binance Adapter for fetching historical and real-time data.

from data.api_adapters.ccxt_adapter import CCXTAdapter
from datetime import datetime, timedelta, timezone

print("\n--- Testing CCXT Adapter (Historical - Binance) ---")
binance_adapter = CCXTAdapter('binance') # Or 'coinbasepro', 'kraken', etc.

end_date_crypto = datetime.now(timezone.utc)
start_date_crypto = end_date_crypto - timedelta(days=7) # Last 7 days

df_btc = binance_adapter.fetch_historical_data('BTC/USDT', start_date_crypto, end_date_crypto, '1d')
if not df_btc.empty:
    print(f"BTC/USDT Historical Data (last 5 rows):\n{df_btc.tail()}")
    print(f"BTC/USDT Data Columns: {df_btc.columns.tolist()}")
    print(f"BTC/USDT Data Index Type: {type(df_btc.index)}")
else:
    print("Failed to fetch BTC/USDT historical data.")
df_invalid_crypto = binance_adapter.fetch_historical_data('INVALID/PAIR', start_date_crypto, end_date_crypto, '1d')
if df_invalid_crypto.empty:
    print("Successfully handled invalid pair for CCXT (returned empty DataFrame).")
    
print("\n--- Testing CCXT Adapter (Real-time - Binance) ---")
df_btc_rt = binance_adapter.fetch_realtime_data('BTC/USDT')
if not df_btc_rt.empty:
    print(f"BTC/USDT Real-time Data:\n{df_btc_rt}")
else:
    print("Failed to fetch BTC/USDT real-time data.")    

