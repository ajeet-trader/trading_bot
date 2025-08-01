import pandas as pd
import numpy as np
from typing import Tuple, Dict
from utils.logger_setup import get_logger

logger = get_logger("error")

class DataProcessor:
    """
    A class to standardize, clean, and validate market data from various sources.
    """
    def __init__(self, price_change_threshold: float = 0.50, volume_spike_threshold: float = 10.0):
        self.price_change_threshold = price_change_threshold
        self.volume_spike_threshold = volume_spike_threshold

    def process_data(self, df: pd.DataFrame, symbol: str) -> Tuple[pd.DataFrame, Dict]:
        quality_metrics = {
            'initial_rows': len(df),
            'missing_values_filled': 0,
            'outliers_corrected': 0,
            'invalid_rows_removed': 0,
            'final_rows': 0
        }

        if df.empty:
            logger.warning(f"Empty DataFrame received for {symbol} - nothing to process.")
            return df, quality_metrics

        try:
            df.columns = [col.lower() for col in df.columns]
            df.index.name = 'timestamp'

            df, missing_info = self._handle_missing_data(df, symbol)
            quality_metrics['missing_values_filled'] = missing_info['filled']
            quality_metrics['invalid_rows_removed'] += missing_info['dropped']

            df, validation_info = self._validate_data(df, symbol)
            quality_metrics['invalid_rows_removed'] += validation_info['removed']

            df, outlier_info = self._handle_outliers(df, symbol)
            quality_metrics['outliers_corrected'] = outlier_info['corrected']

            if df.empty:
                logger.error(f"All rows were removed during processing for {symbol}.")
                return df, quality_metrics

            quality_metrics['final_rows'] = len(df)
            logger.info(f"Successfully processed data for {symbol}. "
                        f"Initial rows: {quality_metrics['initial_rows']}, "
                        f"Final rows: {quality_metrics['final_rows']}")
            return df, quality_metrics
        except Exception as e:
            logger.exception(f"Unexpected error processing data for {symbol}: {e}")
            return pd.DataFrame(), quality_metrics

    def _handle_missing_data(self, df: pd.DataFrame, symbol: str) -> Tuple[pd.DataFrame, Dict]:
        stats = {'filled': 0, 'dropped': 0}
        if df.empty: return df, stats

        initial_missing = df.isna().sum().sum()
        df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].ffill(limit=2)
        df['volume'] = df['volume'].fillna(0)

        stats['filled'] = initial_missing - df.isna().sum().sum()

        initial_rows = len(df)
        df = df.dropna(subset=['open', 'high', 'low', 'close'])
        stats['dropped'] = initial_rows - len(df)

        if stats['filled'] > 0 or stats['dropped'] > 0:
            logger.warning(f"Handled missing data for {symbol}: Filled={stats['filled']}, Dropped={stats['dropped']}")

        return df, stats

    def _validate_data(self, df: pd.DataFrame, symbol: str) -> Tuple[pd.DataFrame, Dict]:
        stats = {'removed': 0}
        if df.empty: return df, stats

        invalid_hl = df['high'] < df['low']
        negative_prices = (df[['open', 'high', 'low', 'close']] <= 0).any(axis=1)
        negative_volume = df['volume'] < 0

        invalid_rows_mask = invalid_hl | negative_prices | negative_volume

        if invalid_rows_mask.any():
            num_removed = invalid_rows_mask.sum()
            stats['removed'] = num_removed
            logger.warning(f"Removing {num_removed} invalid rows for {symbol} "
                           f"(H<L: {invalid_hl.sum()}, NegPrice: {negative_prices.sum()}, NegVol: {negative_volume.sum()})")
            df = df[~invalid_rows_mask]

        return df, stats

    def _handle_outliers(self, df: pd.DataFrame, symbol: str) -> Tuple[pd.DataFrame, Dict]:
        stats = {'corrected': 0}
        if df.empty or df.shape[0] < 5:
            logger.info(f"Skipping outlier detection for {symbol} due to insufficient data ({df.shape[0]} rows).")
            return df, stats

        # Price Outliers
        price_change = df['close'].pct_change().abs()
        price_outliers = price_change > self.price_change_threshold

        if price_outliers.any():
            num_corrected = price_outliers.sum()
            stats['corrected'] += num_corrected
            logger.warning(f"Correcting {num_corrected} price outliers for {symbol}.")
            df.loc[price_outliers, ['open', 'high', 'low', 'close']] = np.nan
            df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].ffill()

        # Volume Outliers
        window_size = min(20, len(df))
        rolling_vol = df['volume'].rolling(window=window_size, min_periods=3).mean()
        volume_outliers = (df['volume'] > rolling_vol * self.volume_spike_threshold) & (rolling_vol > 0)

        if volume_outliers.any():
            num_corrected = volume_outliers.sum()
            stats['corrected'] += num_corrected
            logger.warning(f"Capping {num_corrected} volume outliers for {symbol}.")
            df.loc[volume_outliers, 'volume'] = rolling_vol[volume_outliers] * self.volume_spike_threshold

        return df, stats
