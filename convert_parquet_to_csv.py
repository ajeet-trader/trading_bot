import pandas as pd

# Adjust the path if needed
parquet_path = "data/processed/1d/AAPL.parquet"
csv_path = "data/processed/1d/AAPL.csv"

# Load and convert
df = pd.read_parquet(parquet_path)
df.to_csv(csv_path)

print(f"✅ Converted '{parquet_path}' to '{csv_path}'")
