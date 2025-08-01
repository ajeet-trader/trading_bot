import pandas as pd
import pandas_ta as ta
from typing import List
from strategies.base_strategy import BaseStrategy
from utils.data_structures import Signal
from strategies import register_strategy

@register_strategy
class BollingerBands(BaseStrategy):
    """
    Bollinger Bands mean-reversion strategy.
    Generates BUY signals when price touches or crosses below the lower band.
    Generates SELL signals when price touches or crosses above the upper band.
    """
    name = "bollinger_bands"
    description = "Bollinger Bands Mean Reversion Strategy"
    param_definitions = {
        "bb_period": (int, 20, None),
        "bb_std_dev": (float, 2.0, None),
    }

    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        # Calculate Bollinger Bands
        data.ta.bbands(length=self.config.params['bb_period'], std=self.config.params['bb_std_dev'], append=True)
        lower_band_col = f"BBL_{self.config.params['bb_period']}_{self.config.params['bb_std_dev']}"
        upper_band_col = f"BBU_{self.config.params['bb_period']}_{self.config.params['bb_std_dev']}"

        signals = []
        for i in range(1, len(data)):
            # BUY signal: Price crosses below the lower band
            if data['close'].iloc[i-1] > data[lower_band_col].iloc[i-1] and data['close'].iloc[i] <= data[lower_band_col].iloc[i]:
                signals.append(self._create_signal(
                    timestamp=data.index[i],
                    signal_type="BUY",
                    price=data['close'].iloc[i]
                ))
            # SELL signal: Price crosses above the upper band
            elif data['close'].iloc[i-1] < data[upper_band_col].iloc[i-1] and data['close'].iloc[i] >= data[upper_band_col].iloc[i]:
                signals.append(self._create_signal(
                    timestamp=data.index[i],
                    signal_type="SELL",
                    price=data['close'].iloc[i]
                ))
        return signals