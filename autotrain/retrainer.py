import sys
from pathlib import Path

# Add project root to Python path for relative imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

import json
from datetime import datetime, timedelta
from pathlib import Path
import sys
# Adjust sys.path to allow imports from the project root
# This is crucial for scripts run directly from their own directory
project_root_path = Path(__file__).resolve().parent.parent
if str(project_root_path) not in sys.path:
    sys.path.append(str(project_root_path))
from data.api_adapters.yahoo_finance_adapter import YahooFinanceAdapter
from data.data_processor import DataProcessor
from data.data_storage import DataStorage
from ai_models.feature_engineering import FeatureEngineer
from ai_models.model_trainer import ModelTrainer
from ai_models.model_registry import ModelRegistry
from utils.logger_setup import get_logger
class AutoRetrainer:
    """
    Orchestrates the automated retraining of ML models.
    This class combines various components of the trading system to fetch fresh data,
    process it, generate features, and retrain models.
    """
    def __init__(self, retrain_schedule_days: int, performance_threshold: float):
        """
        Initializes the AutoRetrainer with thresholds for triggering retraining.
        Args:
            retrain_schedule_days (int): Minimum number of days before a model should be considered for retraining.
            performance_threshold (float): Percentage degradation in performance that triggers retraining (e.g., 0.05 for 5%).
        """
        self.retrain_schedule_days = retrain_schedule_days
        self.performance_threshold = performance_threshold
        
        # Compose instances of all the necessary modules from our system
        self.data_adapter = YahooFinanceAdapter() # Assuming Yahoo Finance for data source in retraining
        self.data_processor = DataProcessor()
        self.data_storage = DataStorage()
        self.feature_engineer = FeatureEngineer()
        self.model_registry = ModelRegistry()
        self.model_trainer = ModelTrainer(self.model_registry)
        
        # Path to where feature-engineered data is saved
        self.features_data_path = project_root_path / "data" / "features"
        self.logger = get_logger("error") # Use the error logger for retraining events
    def get_model_metadata(self, symbol: str, interval: str) -> list:
        """
        Retrieves all available metadata for models trained for a specific symbol and interval.
        This helps in determining the last training date and historical performance.
        """
        safe_symbol = symbol.replace('/', '_') # Sanitize symbol for filename
        # Get all metadata files for this symbol-interval combination
        model_files = self.model_registry.registry_path.glob(f"{safe_symbol}_{interval}_*_metadata.json")
        metadata_list = []
        for file in model_files:
            try:
                with open(file, 'r') as f:
                    metadata_list.append(json.load(f))
            except json.JSONDecodeError as e:
                self.logger.error(f"Error decoding JSON from metadata file {file}: {e}")
        return metadata_list
    def check_retraining_trigger(self, 
                                 symbol: str, 
                                 interval: str, 
                                 days_since_last_train: int,
                                 performance_degradation: float) -> bool:
        """
        Checks if the conditions for retraining a model have been met.
        Args:
            symbol (str): The trading symbol the model applies to.
            interval (str): The data interval the model uses.
            days_since_last_train (int): Number of days elapsed since the model was last trained.
            performance_degradation (float): A metric indicating the current performance drop 
                                             relative to historical best (e.g., 0.1 for 10% degradation).
        Returns:
            bool: True if the model should be retrained based on the defined triggers, False otherwise.
        """
        # Trigger 1: Time-based schedule
        if days_since_last_train > self.retrain_schedule_days:
            self.logger.info(f"RETRAIN TRIGGER (Time-based): Model for {symbol} ({interval}) is older than scheduled ({self.retrain_schedule_days} days). Last trained {days_since_last_train} days ago.")
            return True
        
        # Trigger 2: Performance-based degradation
        if performance_degradation > self.performance_threshold:
            self.logger.warning(f"RETRAIN TRIGGER (Performance-based): Performance degradation for {symbol} ({interval}) is {performance_degradation:.2%} which exceeds threshold of {self.performance_threshold:.2%}.")
            return True
            
        return False
    def run_retraining_pipeline(self, symbol: str, interval: str):
        """
        Executes the full data fetching, feature engineering, and model training pipeline.
        This updates the models in the registry with fresh data.
        """
        print(f"\n--- Starting Retraining Pipeline for {symbol} {interval} ---")
        self.logger.info(f"Initiating full retraining pipeline for {symbol} {interval}.")
        
        try:
            # 1. Fetch latest raw data from the adapter
            print("Step 1: Fetching latest data...")
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365 * 2) # Fetch 2 years of historical data for retraining
            raw_data = self.data_adapter.fetch_historical_data(symbol, start_date, end_date, interval)
            if raw_data.empty:
                print("Failed to fetch data or no new data available. Aborting retraining.")
                self.logger.warning(f"No new raw data for {symbol} {interval}. Retraining aborted.")
                return
            self.logger.info(f"Fetched {len(raw_data)} rows of raw data for {symbol}.")
            # 2. Process (clean and normalize) the raw data
            print("Step 2: Processing data...")
            processed_data, processing_metrics = self.data_processor.process_data(raw_data, symbol)
            if processed_data.empty:
                print("Processing resulted in empty data. Aborting retraining.")
                self.logger.error(f"Processed data for {symbol} {interval} is empty. Retraining aborted.")
                return
            self.logger.info(f"Processed data for {symbol}. Final rows: {len(processed_data)}. Metrics: {processing_metrics}")
            
            # 3. Save the processed data to the data storage
            # (Optional, but good practice to keep processed data up-to-date)
            self.data_storage.save_data(processed_data, symbol, interval)
            self.logger.info(f"Saved processed data for {symbol}.")
            
            # 4. Engineer features from the processed data
            print("Step 4: Engineering features...")
            feature_df = self.feature_engineer.generate_features(processed_data)
            if feature_df.empty:
                print("Feature engineering resulted in empty data. Aborting retraining.")
                self.logger.error(f"Feature-engineered data for {symbol} {interval} is empty. Retraining aborted.")
                return
            
            # Save the new feature set (overwrites old one)
            self.features_data_path.mkdir(parents=True, exist_ok=True)
            features_file = self.features_data_path / f"{symbol.replace('/', '_')}_{interval}_features.parquet"
            feature_df.to_parquet(features_file)
            self.logger.info(f"Engineered and saved {len(feature_df.columns)} features for {symbol}.")
            # 5. Train new models using the updated features
            print("Step 5: Training new models...")
            # 'xgb' and 'lgbm' are typically good general-purpose models
            trained_model_metrics = self.model_trainer.train_and_evaluate(
                symbol=symbol, interval=interval, model_types=['xgb', 'lgbm']
            )
            
            print("\n--- Retraining Pipeline Complete ---")
            self.logger.info(f"Retraining pipeline for {symbol} {interval} successfully completed.")
            print("New models have been trained and saved to the registry.")
            print("Summary of new model performance:")
            for model_name, model_metrics in trained_model_metrics.items():
                print(f"  - {model_name}: Accuracy={model_metrics['accuracy']:.2%}, Precision={model_metrics['precision']:.2%}")
        except Exception as e:
            self.logger.exception(f"An unexpected error occurred during the retraining pipeline for {symbol} {interval}: {e}")
            print(f"An error occurred during retraining. Check the logs for details.")
# Example usage for direct execution and testing of the AutoRetrainer
if __name__ == "__main__":
    print("--- Testing AutoRetrainer Module ---")
    
    # 1. Initialize the Retrainer with example parameters
    # In a real deployed system, these would come from config.yaml
    retrainer = AutoRetrainer(
        retrain_schedule_days=30, # Consider retraining if model is older than 30 days
        performance_threshold=0.10 # Consider retraining if performance drops by more than 10%
    )
    
    symbol_to_check = 'AAPL' # Use a symbol that you have already processed data for
    interval_to_check = '1d'
    print(f"\n--- Checking if retraining is needed for {symbol_to_check} ({interval_to_check}) ---")
    
    # Simulate finding the latest model's training date
    metadata_list = retrainer.get_model_metadata(symbol_to_check, interval_to_check)
    if metadata_list:
        # Sort by saved_at timestamp (ISO format) to get the most recent model
        latest_metadata = sorted(metadata_list, key=lambda x: x.get('saved_at', ''), reverse=True)[0]
        last_train_date_str = latest_metadata.get('saved_at')
        if last_train_date_str:
            # Parse the ISO format string to a datetime object
            last_train_date = datetime.fromisoformat(last_train_date_str)
            days_since_training = (datetime.now() - last_train_date).days
            print(f"Last training for {symbol_to_check} was on {last_train_date.strftime('%Y-%m-%d')} ({days_since_training} days ago).")
        else:
            days_since_training = 9999 # Treat as very old if timestamp is missing
            print("No valid training date found in metadata. Assuming model is very old.")
    else:
        days_since_training = 9999 # No model exists at all, force training
        print(f"No existing model found in the registry for {symbol_to_check} ({interval_to_check}).")
    # Simulate a performance degradation metric (in a real system, this would be computed by a monitoring service)
    # For this test, we'll use a mock value.
    mock_performance_degradation = 0.03 # Example: 3% performance drop (below 10% threshold)
    print(f"Simulated current performance degradation: {mock_performance_degradation:.2%}")
    
    # 3. Check the trigger using the `check_retraining_trigger` method
    should_retrain = retrainer.check_retraining_trigger(
        symbol=symbol_to_check,
        interval=interval_to_check,
        days_since_last_train=days_since_training,
        performance_degradation=mock_performance_degradation
    )
    
    # 4. Run the retraining pipeline if triggered
    if should_retrain:
        print("\nRetraining trigger met. Running retraining pipeline...")
        retrainer.run_retraining_pipeline(symbol_to_check, interval_to_check)
    else:
        print("\nNo retraining trigger met based on current conditions. Existing models will continue to be used.")
        
    # --- Force a retraining trigger for demonstration purposes ---
    # This simulates a scenario where you *know* you need to retrain, regardless of current metrics.
    print("\n--- Forcing a retraining trigger for demonstration (e.g., if you manually know a major market shift occurred) ---")
    forced_retrain_days = 99 # Artificially make it older than schedule
    forced_degradation = 0.0 # No degradation, but time trigger should still fire
    should_retrain_forced = retrainer.check_retraining_trigger(
        symbol=symbol_to_check,
        interval=interval_to_check,
        days_since_last_train=forced_retrain_days,
        performance_degradation=forced_degradation
    )
    if should_retrain_forced:
        print("Forced retraining trigger met. Running retraining pipeline...")
        retrainer.run_retraining_pipeline(symbol_to_check, interval_to_check)
    else:
        print("Forced trigger did not fire, something is wrong with the test logic.")
    print("\n--- AutoRetrainer Module Test Complete ---")