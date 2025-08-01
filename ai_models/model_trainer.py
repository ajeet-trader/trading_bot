import sys
from pathlib import Path
# Add project root to Python path for relative imports
sys.path.append(str(Path(__file__).resolve().parent.parent))


import pandas as pd
from pathlib import Path
from typing import List, Dict
from datetime import datetime

from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier

from ai_models.model_registry import ModelRegistry

class ModelTrainer:
    """
    Handles the training, evaluation, and saving of ML models.
    """
    def __init__(self, registry: ModelRegistry):
        self.registry = registry
        self.models = {
            'xgb': XGBClassifier(use_label_encoder=False, eval_metric='logloss'),
            'lgbm': LGBMClassifier(),
            'random_forest': RandomForestClassifier()
        }

    def _load_feature_data(self, symbol: str, interval: str) -> pd.DataFrame:
        """Loads feature-engineered data."""
        features_path = Path(__file__).parent.parent / "data" / "features"
        safe_symbol = symbol.replace('/', '_')
        feature_file = features_path / f"{safe_symbol}_{interval}_features.parquet"
        if not feature_file.exists():
            raise FileNotFoundError(f"Feature file not found: {feature_file}")
        return pd.read_parquet(feature_file)

    def train_and_evaluate(self, 
                           symbol: str, 
                           interval: str, 
                           model_types: List[str] = ['xgb', 'lgbm'],
                           test_size: float = 0.2) -> Dict[str, Dict]:
        """
        Trains multiple models and returns their performance metrics.
        """
        # 1. Load data and define features (X) and target (y)
        feature_df = self._load_feature_data(symbol, interval)
        X = feature_df.drop(columns=['target'])
        y = feature_df['target']

        # 2. Perform time-series split (no shuffling)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, shuffle=False
        )
        print(f"Data split: {len(X_train)} training samples, {len(y_test)} testing samples.")

        # 3. Train each model
        all_metrics = {}
        for model_type in model_types:
            print(f"\n--- Training model: {model_type} ---")
            model = self.models.get(model_type)
            if model is None:
                print(f"Warning: Unknown model type '{model_type}'. Skipping.")
                continue

            # Train the model
            model.fit(X_train, y_train)
            
            # Evaluate the model
            y_pred = model.predict(X_test)
            metrics = {
                'accuracy': accuracy_score(y_test, y_pred),
                'precision': precision_score(y_test, y_pred),
                'recall': recall_score(y_test, y_pred),
                'training_date': datetime.now().isoformat(),
                'train_size': len(X_train),
                'test_size': len(X_test),
                'features_used': list(X.columns)
            }
            
            # Save the trained model to the registry
            model_name = f"{symbol.replace('/', '_')}_{interval}_{model_type}"
            self.registry.save_model(model, model_name, metrics)
            all_metrics[model_name] = metrics
            
        return all_metrics

# Example usage for direct execution and testing
if __name__ == "__main__":
    # This assumes you have run feature_engineering.py first
    
    # 1. Initialize the registry and trainer
    registry = ModelRegistry()
    trainer = ModelTrainer(registry)
    
    # 2. Train models for a specific symbol
    try:
        metrics = trainer.train_and_evaluate(
            symbol='AAPL',
            interval='1d',
            model_types=['xgb', 'lgbm']
        )
        
        # 3. Print summary
        print("\n\n--- Model Training Summary ---")
        for model_name, model_metrics in metrics.items():
            print(f"\nModel: {model_name}")
            print(f"  Accuracy: {model_metrics['accuracy']:.2%}")
            print(f"  Precision: {model_metrics['precision']:.2%}")
            print(f"  Recall: {model_metrics['recall']:.2%}")
        print("\n✅ Model training and evaluation complete.")
        
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print("Please run `ai_models/feature_engineering.py` first to generate the required data.")