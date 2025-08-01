import pandas as pd
import pandas_ta as ta
from typing import List
from strategies.base_strategy import BaseStrategy
from utils.data_structures import Signal
from strategies import register_strategy

@register_strategy
class MeanReversion(BaseStrategy):
    """
    A simple mean reversion strategy based on Z-score.
    Generates BUY signals when the price is significantly below its rolling mean.
    Generates SELL signals when the price is significantly above its rolling mean.
    """
    name = "mean_reversion"
    description = "Z-Score Based Mean Reversion Strategy"
    param_definitions = {
        "window": (int, 20, None),
        "z_score_threshold": (float, 2.0, None),
    }

    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        # Calculate rolling mean and standard deviation
        rolling_mean = data['close'].rolling(window=self.config.params['window']).mean()
        rolling_std = data['close'].rolling(window=self.config.params['window']).std()

        # Calculate Z-score
        z_score = (data['close'] - rolling_mean) / rolling_std

        signals = []
        for i in range(1, len(data)):
            prev_z = z_score.iloc[i-1]
            curr_z = z_score.iloc[i]

            # BUY signal: Z-score crosses below the negative threshold
            if prev_z > -self.config.params['z_score_threshold'] and curr_z <= -self.config.params['z_score_threshold']:
                signals.append(self._create_signal(
                    timestamp=data.index[i],
                    signal_type="BUY",
                    price=data['close'].iloc[i]
                ))
            # SELL signal: Z-score crosses above the positive threshold
            elif prev_z < self.config.params['z_score_threshold'] and curr_z >= self.config.params['z_score_threshold']:
                signals.append(self._create_signal(
                    timestamp=data.index[i],
                    signal_type="SELL",
                    price=data['close'].iloc[i]
                ))
        return signals