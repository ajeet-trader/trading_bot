from typing import List
import pandas as pd
import pandas_ta as ta # Using pandas_ta for convenience
from strategies.base_strategy import BaseStrategy, StrategyConfig
from utils.data_structures import Signal
from strategies import register_strategy

@register_strategy
class EMACrossover(BaseStrategy):
    """
    A simple Exponential Moving Average (EMA) Crossover strategy.
    Generates BUY signals when the short-period EMA crosses above the long-period EMA,
    and SELL signals when it crosses below.
    """
    name = "ema_crossover"
    description = "EMA Crossover (short EMA crosses long EMA)"
    param_definitions = {
        "short_window": (int, 20, None),
        "long_window": (int, 50, None),
    }

    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """
        Calculates EMAs and generates signals based on their crossover points.
        """
        # Ensure data is sorted by timestamp
        data = data.sort_index()

        # Get parameters from config
        short_window = self.config.params['short_window']
        long_window = self.config.params['long_window']

        # Use pandas_ta to calculate EMAs
        data.ta.ema(length=short_window, append=True)
        data.ta.ema(length=long_window, append=True)
        
        # Find crossover points
        # A positive value indicates short EMA is above long EMA (uptrend)
        # A negative value indicates short EMA is below long EMA (downtrend)
        ema_diff = data[f'EMA_{short_window}'] - data[f'EMA_{long_window}']
        
        # A crossover occurs when the sign of the difference changes
        # `np.sign` returns -1, 0, or 1. `diff()` calculates the change from the previous row.
        # A change from -1 to 1 is a BUY signal (diff = 2).
        # A change from 1 to -1 is a SELL signal (diff = -2).
        crossover = ema_diff.apply(lambda x: 1 if x > 0 else -1).diff()

        signals = []
        for i in range(len(crossover)):
            if crossover.iloc[i] == 2: # BUY signal
                signal = self._create_signal(
                    timestamp=crossover.index[i],
                    signal_type="BUY",
                    price=data['close'].iloc[i]
                )
                signals.append(signal)
            elif crossover.iloc[i] == -2: # SELL signal
                signal = self._create_signal(
                    timestamp=crossover.index[i],
                    signal_type="SELL",
                    price=data['close'].iloc[i]
                )
                signals.append(signal)
                
        return signals