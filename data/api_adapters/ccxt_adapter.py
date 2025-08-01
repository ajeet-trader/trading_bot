import ccxt
import pandas as pd
from datetime import datetime, timezone
from typing import List, Dict
from data.api_adapters.base_adapter import BaseAPIAdapter
from utils.logger_setup import get_logger
from utils.config_loader import config # To get API keys
logger = get_logger("error")
class CCXTAdapter(BaseAPIAdapter):
    """
    Data adapter for cryptocurrency exchanges using the CCXT library.
    Supports various exchanges like Binance, Coinbase Pro, etc.
    """
    def __init__(self, exchange_id: str):
        super().__init__(f"CCXT ({exchange_id})")
        self.exchange_id = exchange_id
        self.exchange = self._initialize_exchange()
        self.symbols_cache: List[str] = []
    def _initialize_exchange(self):
        """Initializes the CCXT exchange object with API keys from config."""
        try:
            exchange_class = getattr(ccxt, self.exchange_id)
            api_keys = config.get('api_keys', {})
            
            # CCXT expects specific key names, adjust based on exchange
            # Example for Binance:
            if self.exchange_id == 'binance':
                api_key = api_keys.get('binance_api_key')
                api_secret = api_keys.get('binance_api_secret')
                if not api_key or not api_secret:
                    logger.warning(f"Binance API keys not found in config. Trading functions may be limited.")
                    return exchange_class({'enableRateLimit': True}) # Public access only
                return exchange_class({
                    'apiKey': api_key,
                    'secret': api_secret,
                    'enableRateLimit': True, # Enable CCXT's rate limit management
                })
            # Add more exchange-specific key handling here if needed
            else:
                return exchange_class({'enableRateLimit': True}) # Default for other exchanges
        except AttributeError:
            logger.error(f"CCXT exchange '{self.exchange_id}' not found.")
            raise
        except Exception as e:
            logger.error(f"Error initializing CCXT exchange {self.exchange_id}: {e}")
            raise
    def fetch_historical_data(self, 
                              symbol: str, 
                              start_date: datetime, 
                              end_date: datetime, 
                              interval: str = '1h') -> pd.DataFrame:
        """
        Fetches historical OHLCV (candlestick) data from a CCXT exchange.
        Args:
            symbol (str): The trading pair (e.g., 'BTC/USDT', 'ETH/USD').
            start_date (datetime): The start date.
            end_date (datetime): The end date.
            interval (str): Candlestick interval (e.g., '1m', '5m', '1h', '1d').
        Returns:
            pd.DataFrame: Standardized DataFrame or empty DataFrame on error/no data.
        """
        if not self.exchange:
            return pd.DataFrame()
        # Convert datetime to milliseconds timestamp for CCXT
        since = int(start_date.timestamp() * 1000)
        
        all_ohlcv = []
        limit = 1000 # Max number of candles per request for most exchanges
        while True:
            try:
                # fetch_ohlcv returns: [timestamp, open, high, low, close, volume]
                ohlcv = self.exchange.fetch_ohlcv(symbol, interval, since, limit)
                if not ohlcv:
                    break
                all_ohlcv.extend(ohlcv)
                
                # Update 'since' to the timestamp of the last fetched candle + 1 interval
                # This ensures we don't refetch the last candle and continue from there
                last_timestamp = ohlcv[-1][0]
                since = last_timestamp + self.exchange.parse_timeframe(interval) * 1000
                
                # Stop if we've fetched beyond the end_date
                if last_timestamp >= int(end_date.timestamp() * 1000):
                    break
                
            except ccxt.NetworkError as e:
                logger.error(f"Network error fetching historical data from {self.name} for {symbol}: {e}")
                break
            except ccxt.ExchangeError as e:
                logger.error(f"Exchange error fetching historical data from {self.name} for {symbol}: {e}")
                break
            except Exception as e:
                logger.error(f"Unexpected error fetching historical data from {self.name} for {symbol}: {e}")
                break
        if not all_ohlcv:
            logger.warning(f"No historical data found for {symbol} from {self.name} for {start_date} to {end_date}")
            return pd.DataFrame()
        df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        # Convert timestamp from milliseconds to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        
        # Filter out data beyond end_date if any were fetched due to batching
        df = df[df['timestamp'] <= end_date]
        df = self._standardize_dataframe(df)
        return df
    def fetch_realtime_data(self, symbol: str) -> pd.DataFrame:
        """
        Fetches the latest ticker information (current price, volume) from a CCXT exchange.
        This typically represents the last traded price and 24h volume.
        """
        if not self.exchange:
            return pd.DataFrame()
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            if not ticker:
                logger.warning(f"No real-time ticker found for {symbol} from {self.name}")
                return pd.DataFrame()
            # CCXT ticker provides 'last' (close), 'open', 'high', 'low', 'volume'
            # We need to construct a DataFrame for consistency
            current_time_utc = datetime.now(timezone.utc)
            data = {
                'timestamp': [current_time_utc],
                'open': [ticker.get('open')],
                'high': [ticker.get('high')],
                'low': [ticker.get('low')],
                'close': [ticker.get('last')],
                'volume': [ticker.get('baseVolume')] # or 'volume' depending on exchange
            }
            df = pd.DataFrame(data).set_index('timestamp')
            df = self._standardize_dataframe(df)
            return df
        except ccxt.NetworkError as e:
            logger.error(f"Network error fetching real-time data from {self.name} for {symbol}: {e}")
            return pd.DataFrame()
        except ccxt.ExchangeError as e:
            logger.error(f"Exchange error fetching real-time data from {self.name} for {symbol}: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Unexpected error fetching real-time data from {self.name} for {symbol}: {e}")
            return pd.DataFrame()
    def get_available_symbols(self) -> List[str]:
        """
        Fetches a list of available trading symbols (markets) from the exchange.
        Caches the result after the first fetch.
        """
        if not self.symbols_cache:
            if not self.exchange:
                return []
            try:
                markets = self.exchange.load_markets()
                self.symbols_cache = list(markets.keys())
                logger.info(f"Loaded {len(self.symbols_cache)} symbols for {self.name}.")
            except ccxt.NetworkError as e:
                logger.error(f"Network error fetching symbols from {self.name}: {e}")
            except ccxt.ExchangeError as e:
                logger.error(f"Exchange error fetching symbols from {self.name}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error fetching symbols from {self.name}: {e}")
        return self.symbols_cache