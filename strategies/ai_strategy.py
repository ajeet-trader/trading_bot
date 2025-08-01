import pandas as pd
from typing import List, Dict, Any
from strategies.base_strategy import BaseStrategy, StrategyConfig
from utils.data_structures import Signal
from strategies import register_strategy
from ai_models.model_registry import ModelRegistry
from ai_models.feature_engineering import FeatureEngineer
@register_strategy
class AIStrategy(BaseStrategy):
    """
    A strategy that uses a pre-trained machine learning model to generate signals.
    """
    name = "ai_strategy"
    description = "Generates signals based on predictions from a trained ML model."
    param_definitions = {
        "model_name": (str, "default_model_name", None),
        "confidence_threshold": (float, 0.5, 1.0),
    }
    def __init__(self, config: StrategyConfig, symbol: str):
        """
        Initializes the AI-driven strategy by loading the specified ML model.
        """
        super().__init__(config, symbol)
        self.model_name = self.config.params.get("model_name")
        if not self.model_name:
            raise ValueError("AI strategy config must include a 'model_name' parameter.")
        
        # Load the specified model from the registry
        registry = ModelRegistry()
        self.model, self.metadata = registry.load_latest_model(self.model_name)
        if self.model is None:
            raise FileNotFoundError(f"Could not load model '{self.model_name}' from registry.")
        
        training_date = self.metadata.get('metrics', {}).get('training_date', 'N/A')
        print(f"AI Strategy '{self.name}' initialized with model trained on {training_date}")
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """
        Generates signals using the loaded machine learning model.
        """
        # 1. Engineer features for the input data, just like during training
        feature_engineer = FeatureEngineer()
        feature_df = feature_engineer.generate_features(data.copy())
        
        # Ensure the data has the exact same columns the model was trained on
        model_features = self.metadata.get('metrics', {}).get('features_used', [])
        if not model_features:
            raise ValueError("Model metadata does not contain the list of features used for training.")
        
        # Align columns, filling missing ones with 0 (if any)
        X = feature_df.reindex(columns=model_features, fill_value=0)
        
        # 2. Get model predictions and probabilities
        predictions = self.model.predict(X)
        probabilities = self.model.predict_proba(X) # Shape: (n_samples, n_classes)
        # 3. Create signals based on predictions and confidence
        signals = []
        confidence_threshold = self.config.params.get("confidence_threshold", 0.5)
        for i in range(len(X)):
            prediction = predictions[i]
            # Confidence is the probability of the predicted class
            confidence = probabilities[i][prediction] 
            if confidence >= confidence_threshold:
                # A prediction of 1 means 'UP', so we BUY.
                # A prediction of 0 means 'NOT UP', so we SELL (or exit a long position).
                signal_type = 'BUY' if prediction == 1 else 'SELL'
                
                signals.append(self._create_signal(
                    timestamp=X.index[i],
                    signal_type=signal_type,
                    price=data.loc[X.index[i], 'close'],
                    confidence=float(confidence) # Ensure it's a standard float
                ))
                
        return signals