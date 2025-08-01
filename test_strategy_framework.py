from strategies import get_strategy_class
from strategies.base_strategy import StrategyConfig
from data.data_storage import DataStorage
import pandas as pd

def test_ema_crossover():
    print("--- Testing EMA Crossover Strategy Framework ---")
    
    # 1. Load test data (we'll use the AAPL data we saved in Phase 2)
    storage = DataStorage()
    data = storage.load_data('AAPL', '1d')
    assert not data.empty, "Failed to load test data for AAPL."
    print(f"Loaded {len(data)} rows of AAPL data.")
    
    # 2. Get the strategy class from the registry
    StrategyClass = get_strategy_class("ema_crossover")
    print(f"Successfully retrieved strategy class: {StrategyClass.name}")
    
    # 3. Create a configuration for the strategy
    config = StrategyConfig(
        name="ema_crossover",
        params={"short_window": 10, "long_window": 25}, # Use different params for testing
        enabled=True
    )
    
    # 4. Initialize the strategy instance
    strategy = StrategyClass(config, symbol='AAPL')
    
    # 5. Generate signals
    print("Generating signals...")
    signals = strategy.generate_signals(data)
    print(f"Generated {len(signals)} signals.")
    
    # 6. Validate the output
    assert len(signals) > 0, "Test failed: No signals were generated."
    first_signal = signals[0]
    assert first_signal.strategy == "ema_crossover", "Signal has incorrect strategy name."
    assert first_signal.symbol == "AAPL", "Signal has incorrect symbol."
    print("First generated signal:", first_signal)
    print("✅ Validation successful! Check logs/signal.log for detailed output.")

if __name__ == "__main__":
    # Make sure to import the strategy module so it gets registered
    import strategies.ema_crossover
    test_ema_crossover()