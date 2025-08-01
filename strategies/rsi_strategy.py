import pandas as pd
import pandas_ta as ta
from typing import List
from strategies.base_strategy import BaseStrategy
from utils.data_structures import Signal
from strategies import register_strategy

@register_strategy
class RSIStrategy(BaseStrategy):
    """
    Relative Strength Index (RSI) strategy.
    Generates BUY signals when RSI crosses up from oversold and
    SELL signals when RSI crosses down from overbought.
    """
    name = "rsi_strategy"
    description = "RSI Overbought/Oversold Strategy"
    param_definitions = {
        "rsi_period": (int, 14, None),
        "oversold_threshold": (int, 30, 100),
        "overbought_threshold": (int, 70, 100),
    }

    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        # Calculate RSI
        data.ta.rsi(length=self.config.params['rsi_period'], append=True)
        rsi_col = f"RSI_{self.config.params['rsi_period']}"

        signals = []
        for i in range(1, len(data)):
            prev_rsi = data[rsi_col].iloc[i-1]
            curr_rsi = data[rsi_col].iloc[i]

            # BUY signal: RSI crosses above oversold threshold
            if prev_rsi <= self.config.params['oversold_threshold'] and curr_rsi > self.config.params['oversold_threshold']:
                signals.append(self._create_signal(
                    timestamp=data.index[i],
                    signal_type="BUY",
                    price=data['close'].iloc[i]
                ))
            # SELL signal: RSI crosses below overbought threshold
            elif prev_rsi >= self.config.params['overbought_threshold'] and curr_rsi < self.config.params['overbought_threshold']:
                signals.append(self._create_signal(
                    timestamp=data.index[i],
                    signal_type="SELL",
                    price=data['close'].iloc[i]
                ))
        return signals