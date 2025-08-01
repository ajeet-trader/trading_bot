import sys
from pathlib import Path
# Add project root to Python path for relative imports
sys.path.append(str(Path(__file__).resolve().parent.parent))


import joblib
from pathlib import Path
from typing import Dict, Any, Tuple
import json
from datetime import datetime

class ModelRegistry:
    """
    Manages saving and loading of trained machine learning models and their metadata.
    """
    def __init__(self, registry_path: str = "ai_models/registry/saved_models"):
        """
        Initializes the ModelRegistry.
        """
        # Note: The path is relative to this file's location
        self.registry_path = Path(__file__).parent / "saved_models"
        self.registry_path.mkdir(parents=True, exist_ok=True)

    def save_model(self, model: Any, model_name: str, metrics: Dict[str, Any]):
        """
        Saves a trained model and its metadata to the registry.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_model_name = model_name.replace('/', '_')
        
        # Save the model object
        model_filename = f"{safe_model_name}_{timestamp}.joblib"
        model_filepath = self.registry_path / model_filename
        joblib.dump(model, model_filepath)
        
        # Save the metadata
        metadata = {
            'model_name': model_name,
            'saved_at': timestamp,
            'metrics': metrics,
            'model_filepath': str(model_filepath)
        }
        metadata_filename = f"{safe_model_name}_{timestamp}_metadata.json"
        metadata_filepath = self.registry_path / metadata_filename
        with open(metadata_filepath, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        print(f"Saved model '{model_name}' to: {model_filepath}")

    def load_latest_model(self, model_name: str) -> Tuple[Any, Dict]:
        """
        Loads the most recent version of a model from the registry.
        """
        safe_model_name = model_name.replace('/', '_')
        model_files = sorted(self.registry_path.glob(f"{safe_model_name}_*.joblib"), reverse=True)
        
        if not model_files:
            print(f"No model found for name '{model_name}' in registry.")
            return None, None
            
        latest_model_path = model_files[0]
        model = joblib.load(latest_model_path)
        
        # Load corresponding metadata
        metadata_path = latest_model_path.with_suffix('.json').with_name(latest_model_path.stem + '_metadata.json')
        metadata = {}
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                
        print(f"Loaded model '{model_name}' from: {latest_model_path}")
        return model, metadata

# Example usage for direct execution and testing
if __name__ == '__main__':
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.datasets import make_classification

    print("--- Testing Model Registry ---")
    # 1. Create a dummy model
    X, y = make_classification(n_samples=100, n_features=4, random_state=42)
    dummy_model = RandomForestClassifier().fit(X, y)
    
    # 2. Initialize registry and save the model
    registry = ModelRegistry()
    registry.save_model(
        model=dummy_model,
        model_name="test_dummy_model",
        metrics={"accuracy": 0.98, "feature_set": "dummy_v1"}
    )
    
    # 3. Load the model back
    loaded_model, metadata = registry.load_latest_model("test_dummy_model")
    
    assert loaded_model is not None, "Failed to load model."
    assert metadata['metrics']['accuracy'] == 0.98, "Metadata mismatch."
    print("\nLoaded Model Metadata:")
    print(json.dumps(metadata, indent=2))
    print("\n✅ Model Registry test successful!")