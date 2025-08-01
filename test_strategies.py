from strategies import get_strategy_class
from strategies.base_strategy import StrategyConfig
from data.data_storage import DataStorage
from utils.config_loader import config as global_config
import pandas as pd

# Import all new strategy modules to ensure they are registered
import strategies.ema_crossover
import strategies.rsi_strategy
import strategies.bollinger_bands
import strategies.mean_reversion

def run_strategy_test(strategy_name: str, data: pd.DataFrame):
    """Helper function to test a single strategy."""
    print(f"\n--- Testing Strategy: {strategy_name} ---")
    
    # Find the strategy's config in the global config file
    strategy_config_dict = next((item for item in global_config['strategies'] if item['name'] == strategy_name), None)
    assert strategy_config_dict is not None, f"Config for {strategy_name} not found in config.yaml"
    
    # 1. Get strategy class from registry
    StrategyClass = get_strategy_class(strategy_name)
    
    # 2. Create config object
    config = StrategyConfig(
        name=strategy_config_dict['name'],
        params=strategy_config_dict['params'],
        enabled=strategy_config_dict['enabled']
    )
    
    # 3. Initialize strategy
    strategy = StrategyClass(config, symbol='AAPL')
    
    # 4. Generate signals
    signals = strategy.generate_signals(data.copy()) # Pass a copy to avoid modifying original data
    print(f"Generated {len(signals)} signals for {strategy_name}.")
    
    # 5. Validate
    assert isinstance(signals, list), f"{strategy_name} did not return a list."
    if len(signals) > 0:
        print(f"First signal: {signals[0]}")
    
    print(f"✅ Test for {strategy_name} passed!")

if __name__ == "__main__":
    # Load test data once
    storage = DataStorage()
    aapl_data = storage.load_data('AAPL', '1d')
    assert not aapl_data.empty, "Failed to load AAPL test data. Make sure you've run the pipeline test first."
    
    # List of strategies to test
    strategies_to_test = [
        "ema_crossover",
        "rsi_strategy",
        "bollinger_bands",
        "mean_reversion"
    ]
    
    for strategy_name in strategies_to_test:
        run_strategy_test(strategy_name, aapl_data)