from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd
from utils.data_structures import Signal
from utils.logger_setup import get_logger

# Use the dedicated signal logger we created in Phase 1
signal_logger = get_logger("signal")

@dataclass
class StrategyConfig:
    """
    A standardized configuration object for a strategy instance.
    """
    name: str
    params: Dict[str, float]
    enabled: bool = True

class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.
    
    Each concrete strategy must:
    1. Inherit from this class.
    2. Be decorated with @register_strategy.
    3. Define `name`, `description`, and `param_definitions`.
    4. Implement the `generate_signals` method.
    """
    name: str = "base_strategy"
    description: str = "Abstract base strategy (override in subclasses)"
    param_definitions: Dict[str, Tuple[type, float, Optional[float]]] = {
        # Format: {"param_name": (type, default_value, optional_max_value)}
    }

    def __init__(self, config: StrategyConfig, symbol: str):
        """
        Initializes the strategy with its configuration and the symbol it will trade.
        """
        self.config = config
        self.symbol = symbol
        self._validate_parameters()
        get_logger("error").info(f"Initialized strategy: {self.name} for {self.symbol} with params: {config.params}")

    def _validate_parameters(self):
        """Validates that all provided parameters match the strategy's definitions."""
        for param_name, (expected_type, _, _) in self.param_definitions.items():
            if param_name not in self.config.params:
                raise ValueError(f"Missing required parameter '{param_name}' for strategy {self.name}.")
            
            param_value = self.config.params[param_name]
            if not isinstance(param_value, expected_type):
                raise TypeError(f"Parameter '{param_name}' for strategy {self.name} must be "
                                f"of type {expected_type.__name__}, but got {type(param_value).__name__}.")

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """
        Generates trading signals based on the provided market data.
        This is the core logic of the strategy.
        """
        pass

    def _create_signal(self, 
                       timestamp: datetime, 
                       signal_type: str, 
                       price: float, 
                       confidence: Optional[float] = None) -> Signal:
        """
        Helper method to create and log a standardized Signal object.
        """
        print(f"Logging signal at {timestamp}")
        signal = Signal(
            timestamp=timestamp,
            symbol=self.symbol,
            strategy=self.name,
            signal_type=signal_type,
            price=price,
            confidence=confidence
        )
        # Log the signal to our dedicated, structured signal log file
        #signal_logger.info("Signal generated", extra={"extra_data": signal.__dict__})
        signal_logger.info("Signal generated", extra={"extra_data": asdict(signal)})

        return signal