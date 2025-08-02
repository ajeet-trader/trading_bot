import os
import pandas as pd
from alpaca_trade_api.rest import REST
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

API_KEY = os.getenv("ALPACA_API_KEY")
API_SECRET = os.getenv("ALPACA_API_SECRET")
BASE_URL = "https://paper-api.alpaca.markets"

# Initialize Alpaca API
api = REST(API_KEY, API_SECRET, base_url=BASE_URL)

# Define output directory
DATA_DIR = Path("alpaca_data")
DATA_DIR.mkdir(exist_ok=True)

def save_to_csv(data, filename):
    path = DATA_DIR / filename
    pd.DataFrame(data).to_csv(path, index=False)
    print(f"[✔] Saved {len(data)} records to '{path}'")

def fetch_equities():
    print("[+] Fetching all active equities...")
    assets = api.list_assets(status="active")
    equities = [a._raw for a in assets if a.tradable]

    # Save all tradable equities
    save_to_csv(equities, "alpaca_equities_all.csv")

    # Filter ETFs
    etfs = [a for a in equities if "ETF" in a['name'].upper()]
    save_to_csv(etfs, "alpaca_etfs.csv")

    # Fractional shares
    fractional = [a for a in equities if a.get('fractionable')]
    save_to_csv(fractional, "alpaca_fractionals.csv")

def fetch_crypto():
    print("[+] Fetching all crypto assets...")
    try:
        crypto_assets = api.get_crypto_assets()
        crypto = [a._raw for a in crypto_assets if a.tradable]
        save_to_csv(crypto, "alpaca_crypto.csv")
    except Exception as e:
        print(f"[!] Failed to fetch crypto assets: {e}")

if __name__ == "__main__":
    fetch_equities()
    fetch_crypto()
