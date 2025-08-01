from typing import Dict, Type

# Forward declaration to avoid circular import
class BaseStrategy:
    pass

STRATEGY_REGISTRY: Dict[str, Type[BaseStrategy]] = {}

def register_strategy(strategy_class: Type[BaseStrategy]):
    """
    A class decorator to register a strategy in the central registry.
    
    Example:
        @register_strategy
        class MyStrategy(BaseStrategy):
            name = "my_strategy"
            ...
    """
    if strategy_class.name in STRATEGY_REGISTRY:
        raise ValueError(f"Duplicate strategy name '{strategy_class.name}' found.")
    STRATEGY_REGISTRY[strategy_class.name] = strategy_class
    return strategy_class

def get_strategy_class(name: str) -> Type[BaseStrategy]:
    """
    Retrieves a strategy class by its unique name from the registry.
    """
    if name not in STRATEGY_REGISTRY:
        raise ValueError(f"Strategy '{name}' not found in registry. Available: {list(STRATEGY_REGISTRY.keys())}")
    return STRATEGY_REGISTRY[name]