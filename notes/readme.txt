```text
SAPIENS AI TRADING BOT

INTELLIGENT, AUTOMATED, MODULAR TRADING SYSTEM

STATUS: Completed
OPTIMIZED FOR: 8GB RAM
POWERED BY: ML / AI

--------------------------------------------------------------------------------

TABLE OF CONTENTS

1. INTRODUCTION
   - SYSTEM GOAL
   - KEY FEATURES
2. CORE PRINCIPLES
3. INSTALLATION & SETUP
4. USAGE (COMMAND LINE INTERFACE - CLI)
5. PROJECT STRUCTURE & FILE REFERENCE
   - ROOT DIRECTORY
   - data/
   - strategies/
   - ai_models/
   - backtest/
   - execution/
   - live_signals/
   - autotrain/
   - utils/
   - logs/
6. FUTURE ENHANCEMENTS
7. CONTRIBUTING
8. LICENSE

--------------------------------------------------------------------------------

1. INTRODUCTION

This project is an intelligent, automated, and modular trading bot system developed in Python. Designed from scratch, it prioritizes efficient operation on local machines with limited resources (e.g., 8GB RAM) while being scalable for real-world deployment. It integrates advanced AI/ML capabilities with a robust trading framework to analyze markets, generate signals, manage risk, and execute trades.

--- SYSTEM GOAL ---
To create a full-featured AI-powered trading platform that:
- Supports multiple financial instruments (forex, crypto, stocks, indices, metals, commodities).
- Implements diverse trading strategies (classic, quantitative, ML/DL, sentiment-based).
- Includes full backtesting, AI/ML signal prediction, live signal generation, and strategy evaluation.
- Utilizes a modular, scalable architecture optimized for low-resource environments.
- Provides historical and real-time signal logging, performance metrics, and risk-adjusted analytics.

--- KEY FEATURES ---
- Modular & Extensible Design: Loose coupling between components for easy modification and expansion.
- Memory Efficiency: Optimized data handling (Parquet, __slots__, chunking) for low RAM usage.
- AI-First Approach: Integrated pipeline for feature engineering, model training, and AI-driven signal generation.
- Comprehensive Data Pipeline: Fetching, cleaning, normalizing, and storing data from various APIs.
- Robust Backtesting: Simulate strategies with realistic costs, and analyze performance with detailed metrics and plots.
- Walk-Forward Optimization: Advanced method to identify robust strategy parameters and mitigate overfitting.
- Risk Management: Dynamic position sizing and portfolio-level circuit breakers to protect capital.
- Paper & Live Execution: Simulated trading environment and integration with real brokerage APIs (e.g., Alpaca).
- Automated Retraining: Pipeline for periodic ML model retraining to adapt to changing market conditions.
- Real-time Monitoring: Interactive web dashboard for live portfolio status, logs, and performance insights.
- CLI Control: All functionalities accessible via a user-friendly command-line interface.

--------------------------------------------------------------------------------

2. CORE PRINCIPLES

- Modularity: Each component has a single, clear responsibility. This ensures maintainability, testability, and scalability.
- Memory Efficiency: All code and data handling are optimized to run smoothly within an 8GB RAM constraint.
- AI-First: The architecture is designed to seamlessly integrate advanced machine learning models into every stage of the trading process.
- Full Logging & Auditing: Every significant event (signal, trade, error) is logged in a structured, machine-readable format for transparency and analysis.
- Continuous Improvement: Built-in mechanisms for automated model retraining and parameter optimization facilitate adaptation and long-term performance.

--------------------------------------------------------------------------------

3. INSTALLATION & SETUP

To get the trading bot up and running, follow these steps:

1.  Clone the repository:
    git clone <repository_url>
    cd sapiens-ai-trading-bot # Or whatever your project root folder is named

2.  Create a Python Virtual Environment:
    It's highly recommended to use a virtual environment to manage dependencies.
    python -m venv venv
    # On Windows:
    .\venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate

3.  Install Dependencies:
    pip install -r requirements.txt

4.  API Key Configuration:
    - Create a .env file in the project's root directory. This file will store your sensitive API keys and SHOULD NOT be committed to version control.
    - Add your API keys to the .env file. Replace placeholders with your actual keys. Example:
      # .env file
      ALPHA_VANTAGE_API_KEY="YOUR_ALPHA_VANTAGE_KEY_HERE"
      BINANCE_API_KEY="YOUR_BINANCE_KEY_HERE"
      BINANCE_API_SECRET="YOUR_BINANCE_SECRET_HERE"
      ALPACA_API_KEY="YOUR_ALPACA_KEY_ID_HERE"
      ALPACA_API_SECRET="YOUR_ALPACA_SECRET_KEY_HERE"
    - Ensure your config.yaml file (also in the root) references these environment variables for API keys. The config_loader will automatically substitute them at runtime.

5.  Initial Data Fetch & Model Training (Recommended):
    Before running backtests or live trading, it's good practice to fetch some data and train initial models.
    # Fetch and process some historical data for AAPL
    python main.py backtest --strategy ema_crossover --symbol AAPL --interval 1d
    # This command will trigger data fetching, processing, and storage.
    # It will also run a backtest and generate reports.

    # Train initial AI models for AAPL (assuming AAPL data is processed)
    python ai_models/model_trainer.py

--------------------------------------------------------------------------------

4. USAGE (COMMAND LINE INTERFACE - CLI)

The bot is controlled via a central main.py CLI in the project root.

python main.py <command> [options]

--- Available Commands ---

- retrain: Retrains AI models with fresh data.
  Example:
    python main.py retrain --symbol NVDA --interval 1d

- backtest: Runs a strategy backtest on historical data.
  Example:
    python main.py backtest --strategy ai_strategy --symbol GOOG --interval 1d

- live: Starts the simplified live trading engine (connects to Alpaca paper account).
  Example:
    python main.py live

- dashboard: Launches the real-time monitoring dashboard in your web browser.
  Example:
    python main.py dashboard

--------------------------------------------------------------------------------

5. PROJECT STRUCTURE & FILE REFERENCE

This section details the purpose of each file, its typical output, and key dependencies for understanding modification impact.

--- ROOT DIRECTORY ---

- File: main.py
  - Purpose: Central Command-Line Interface (CLI) for the entire bot. Acts as the main entry point, parsing commands and orchestrating calls to other modules (backtesting, retraining, live, dashboard).
  - Sample Output / Side Effects:
    - Prints command-specific status messages to console.
    - Triggers processes that generate logs/ entries, backtest/results/ files, etc.
    - Launches web browser for dashboard.
    - Logs "Application starting up." to logs/errors.log.
  - Modification Impact / Dependencies:
    - Depends on almost all top-level modules (e.g., autotrain/retrainer.py, backtest/engine.py, execution/live_integration.py).
    - Changes to argparse configuration or command logic affect how the system is invoked.
    - If strategy names or API key definitions change, this file might need updates to correctly parse arguments or initialize components.

- File: config.yaml
  - Purpose: Global configuration file defining system parameters, API key placeholders, instrument lists, strategy parameters, and risk management rules.
  - Sample Output / Side Effects:
    - No direct output. Consumed by many modules.
  - Modification Impact / Dependencies:
    - Loaded by utils/config_loader.py.
    - High Impact: Changes to parameters here affect the behavior of corresponding modules (e.g., changing ema_crossover parameters changes strategy behavior).
    - If a section or key is renamed/removed, all modules reading that specific key must be updated.

- File: .env
  - Purpose: Secure storage for sensitive API keys and secrets. Loaded by config_loader at runtime.
  - Sample Output / Side Effects:
    - No direct output.
  - Modification Impact / Dependencies:
    - Loaded by utils/config_loader.py.
    - Security Critical: This file should NEVER be committed to version control.
    - Changes to key values here affect API access credentials.
    - Changes to key names require corresponding updates in config.yaml and possibly modules that parse config.yaml values.

- File: requirements.txt
  - Purpose: Lists all Python package dependencies required for the project.
  - Sample Output / Side Effects:
    - No direct output.
  - Modification Impact / Dependencies:
    - Used by pip install -r requirements.txt.
    - Adding/removing libraries requires updating this file and corresponding import statements/code changes in modules using those libraries.

- File: README.md
  - Purpose: This project documentation file.
  - Sample Output / Side Effects:
    - No direct output.
  - Modification Impact / Dependencies:
    - None (except its own accuracy!).

--- data/ ---
This directory manages the data pipeline: fetching, processing, and storing market data.

- File: data/data_processor.py
  - Purpose: Cleans, validates, and normalizes raw market data. Handles missing values, enforces consistent schemas, and detects/corrects outliers.
  - Sample Output / Side Effects:
    - Returns a processed Pandas DataFrame.
    - Logs warnings to logs/errors.log about data quality issues (e.g., missing values, outliers).
  - Modification Impact / Dependencies:
    - Consumes data from data/api_adapters/.
    - Its output (standardized DataFrame) is consumed by data/data_storage.py, ai_models/feature_engineering.py, and autotrain/retrainer.py.
    - Changes to the standardized DataFrame format require updates in all these downstream consumers.

- File: data/data_storage.py
  - Purpose: Manages saving and loading processed data to/from Parquet files. Organizes data by interval and symbol.
  - Sample Output / Side Effects:
    - Creates .parquet files in data/processed/{interval}/ (e.g., data/processed/1d/AAPL_1d.parquet).
    - Returns a Pandas DataFrame when loading.
    - Logs success/failure messages to logs/errors.log.
  - Modification Impact / Dependencies:
    - Consumes processed data from data/data_processor.py.
    - Its output (Parquet files) is consumed by ai_models/feature_engineering.py, backtest/engine.py, and autotrain/retrainer.py.
    - Changes to file paths or the Parquet storage schema affect these consumers.

- Directory: data/api_adapters/
  - Purpose: Directory containing modules for interacting with external data APIs.
  - Sample Output / Side Effects:
    - None.
  - Modification Impact / Dependencies:
    - None.

- File: data/api_adapters/base_adapter.py
  - Purpose: Abstract Base Class (ABC) for all data API adapters. Defines a common interface (methods like fetch_historical_data, fetch_realtime_data).
  - Sample Output / Side Effects:
    - No direct output.
  - Modification Impact / Dependencies:
    - All concrete adapters (yahoo_finance_adapter.py, ccxt_adapter.py, etc.) inherit from it.
    - Changes to abstract methods require updates in all subclasses.

- File: data/api_adapters/yahoo_finance_adapter.py
  - Purpose: Fetches historical and real-time stock data from Yahoo Finance using the yfinance library.
  - Sample Output / Side Effects:
    - Returns Pandas DataFrames with standardized columns.
    - Logs errors/warnings to logs/errors.log on API failures or no data.
  - Modification Impact / Dependencies:
    - Depends on yfinance.
    - Its output is consumed by data/data_processor.py and autotrain/retrainer.py.
    - Changes in its output DataFrame schema (though it aims for standardization) could affect data_processor.py.

- File: data/api_adapters/ccxt_adapter.py
  - Purpose: Fetches historical and real-time cryptocurrency data from various exchanges via the ccxt library.
  - Sample Output / Side Effects:
    - Returns Pandas DataFrames with standardized columns.
    - Logs errors/warnings to logs/errors.log on API failures or no data.
  - Modification Impact / Dependencies:
    - Depends on ccxt and utils/config_loader.py (for API keys).
    - Its output is consumed by data/data_processor.py.
    - Changes in its output DataFrame schema could affect data_processor.py.

--- strategies/ ---
This directory defines the framework for trading strategies and houses their implementations.

- File: strategies/__init__.py
  - Purpose: Manages the strategy registry. Allows strategy classes to be registered and dynamically loaded by name throughout the system.
  - Sample Output / Side Effects:
    - No direct output.
  - Modification Impact / Dependencies:
    - base_strategy.py relies on BaseStrategy type hints.
    - All concrete strategy modules (ema_crossover.py, etc.) use the @register_strategy decorator.
    - backtest/engine.py (and potentially live_signals/dashboard.py) uses get_strategy_class to load strategies.

- File: strategies/base_strategy.py
  - Purpose: Abstract Base Class (ABC) for all trading strategies. Defines the common interface (e.g., generate_signals method), handles parameter validation, and provides a helper for standardized signal creation/logging.
  - Sample Output / Side Effects:
    - No direct output, but its _create_signal helper logs Signal objects to logs/signals.log.
  - Modification Impact / Dependencies:
    - All concrete strategies inherit from it.
    - Depends on utils/data_structures.py (for Signal) and utils/logger_setup.py.
    - Changes to the generate_signals signature or its core logic (e.g., signal creation) affect all inheriting strategies.

- File: strategies/ema_crossover.py
  - Purpose: Implements the EMA Crossover strategy. Generates BUY/SELL signals when short and long EMAs cross.
  - Sample Output / Side Effects:
    - Generates Signal objects.
    - Logs signals to logs/signals.log via base_strategy.py.
  - Modification Impact / Dependencies:
    - Inherits from base_strategy.py.
    - Depends on pandas, pandas_ta.
    - Changes to its param_definitions require updating config.yaml to match.

- File: strategies/rsi_strategy.py
  - Purpose: Implements the RSI (Relative Strength Index) strategy. Generates BUY/SELL signals based on oversold/overbought conditions.
  - Sample Output / Side Effects:
    - Generates Signal objects.
    - Logs signals to logs/signals.log.
  - Modification Impact / Dependencies:
    - Inherits from base_strategy.py.
    - Depends on pandas, pandas_ta.
    - Changes to its param_definitions require updating config.yaml.

- File: strategies/bollinger_bands.py
  - Purpose: Implements the Bollinger Bands strategy. Generates BUY/SELL signals based on price touching/crossing bands.
  - Sample Output / Side Effects:
    - Generates Signal objects.
    - Logs signals to logs/signals.log.
  - Modification Impact / Dependencies:
    - Inherits from base_strategy.py.
    - Depends on pandas, pandas_ta.
    - Changes to its param_definitions require updating config.yaml.

- File: strategies/mean_reversion.py
  - Purpose: Implements a Z-Score based Mean Reversion strategy. Generates BUY/SELL signals when price deviates significantly from its rolling mean.
  - Sample Output / Side Effects:
    - Generates Signal objects.
    - Logs signals to logs/signals.log.
  - Modification Impact / Dependencies:
    - Inherits from base_strategy.py.
    - Depends on pandas, pandas_ta.
    - Changes to its param_definitions require updating config.yaml.

- File: strategies/ai_strategy.py
  - Purpose: Implements an AI-driven strategy. Loads a pre-trained ML model and uses its predictions to generate signals.
  - Sample Output / Side Effects:
    - Generates Signal objects.
    - Logs signals to logs/signals.log.
    - Prints model loading messages to console.
  - Modification Impact / Dependencies:
    - Inherits from base_strategy.py.
    - Depends on ai_models/feature_engineering.py (to generate features at runtime) and ai_models/model_registry.py (to load models).
    - Its param_definitions (specifically model_name) must match a trained model in the registry and config.yaml.

--- ai_models/ ---
This directory contains the core components for AI/ML capabilities, including feature engineering, model training, and model management.

- File: ai_models/feature_engineering.py
  - Purpose: Generates a rich set of features (technical indicators, lagged returns, time-based features, rolling statistics) from processed market data for ML models. Also creates a target variable.
  - Sample Output / Side Effects:
    - Returns a Pandas DataFrame with new feature columns and a target column.
    - Saves .parquet files to data/features/{symbol}_{interval}_features.parquet.
    - Prints summary to console (e.g., number of features, target distribution).
  - Modification Impact / Dependencies:
    - Consumes processed data from data/data_storage.py.
    - Its output is consumed by model_trainer.py.
    - Changes to the feature set (adding/removing features) directly impact the inputs to model_trainer.py.

- File: ai_models/model_trainer.py
  - Purpose: Trains and evaluates machine learning models (XGBoost, LightGBM, RandomForest) on feature-engineered data. Handles train/test split and calls ModelRegistry to save models.
  - Sample Output / Side Effects:
    - Prints training progress and evaluation metrics (accuracy, precision, recall) to console.
    - Saves trained models (.joblib files) and their metadata (.json files) to ai_models/registry/saved_models/.
  - Modification Impact / Dependencies:
    - Consumes feature-engineered data from feature_engineering.py.
    - Depends on sklearn, xgboost, lightgbm, and model_registry.py.
    - Its output (trained models) is primarily used by ai_models/model_registry.py and orchestrated by autotrain/retrainer.py.

- File: ai_models/model_registry.py
  - Purpose: Manages saving, versioning, and loading of trained ML models. Stores models as .joblib files and associated metadata as .json.
  - Sample Output / Side Effects:
    - Saves .joblib model files and .json metadata files to ai_models/registry/saved_models/.
    - Returns loaded model objects and their metadata.
    - Prints model save/load messages to console.
  - Modification Impact / Dependencies:
    - Used by model_trainer.py to save models and by strategies/ai_strategy.py to load models.
    - Changes to the storage format or metadata structure impact both model_trainer.py and ai_strategy.py.

--- backtest/ ---
This directory contains the backtesting engine, performance analytics, and optimization tools.

- File: backtest/engine.py
  - Purpose: Core Backtesting Engine. Simulates trades based on strategy signals against historical data, accounting for costs (commission, slippage) and simple position sizing.
  - Sample Output / Side Effects:
    - Prints backtest progress and summary to console.
    - Saves detailed trade history (portfolio_history) to CSV files in backtest/results/.
    - Returns performance metrics.
  - Modification Impact / Dependencies:
    - Depends on data/data_storage.py, strategies/ (via get_strategy_class), and utils/config_loader.py.
    - Its output (CSV results) is consumed by analytics.py and optimizer.py.
    - Changes to the simulation logic (costs, sizing) directly affect backtest results.

- File: backtest/analytics.py
  - Purpose: Calculates comprehensive performance metrics and generates plots (equity curve, drawdown) from backtest results.
  - Sample Output / Side Effects:
    - Prints detailed performance metrics to console.
    - Saves equity curve and drawdown .png plots to backtest/results/.
  - Modification Impact / Dependencies:
    - Consumes CSV data from engine.py.
    - Depends on matplotlib for plotting.
    - Used by main.py and live_signals/dashboard.py. Changes to metric calculations or plot generation affect how results are displayed/analyzed.

- File: backtest/optimizer.py
  - Purpose: Performs walk-forward optimization for strategies. Systematically tests parameter combinations on out-of-sample data to find robust parameters.
  - Sample Output / Side Effects:
    - Prints optimization progress and best parameters to console.
    - Saves full optimization results to a CSV file in backtest/results/.
    - Saves the best parameter set to a JSON file in backtest/results/.
  - Modification Impact / Dependencies:
    - Depends heavily on engine.py (to run individual backtests) and data/data_storage.py.
    - Uses joblib for parallel processing.
    - Changes to optimization methodology (e.g., how folds are defined, how "best" is selected) impact parameter recommendations.

--- execution/ ---
This directory handles simulated and live trade execution, including critical risk management.

- File: execution/paper_trader.py
  - Purpose: Simulates trade execution and manages a virtual portfolio. Processes signals, calculates positions, and models realistic transaction costs (commission, slippage).
  - Sample Output / Side Effects:
    - Prints updated portfolio status (cash, positions) to console after each simulated trade.
    - Logs simulated trades to logs/trades.log.
  - Modification Impact / Dependencies:
    - Consumes Signal objects.
    - Depends on utils/data_structures.py (for Signal) and utils/logger_setup.py.
    - Depends on risk_manager.py for position sizing and circuit breakers.
    - Changes to trade execution logic or cost modeling affect simulated portfolio performance.

- File: execution/risk_manager.py
  - Purpose: Implements advanced position sizing rules and portfolio-level circuit breakers. Prevents excessive risk by calculating safe trade quantities and halting trading on severe drawdowns.
  - Sample Output / Side Effects:
    - Returns calculated position sizes (float).
    - Logs critical circuit breaker events to logs/errors.log.
    - Prints warnings to console for downsizing trades.
  - Modification Impact / Dependencies:
    - Used by execution/paper_trader.py and execution/live_integration.py.
    - Changes to risk limits (e.g., max_portfolio_risk_per_trade, daily_drawdown_limit) directly affect trading behavior and safety.

- File: execution/live_integration.py
  - Purpose: Provides an interface for live brokerage integration (e.g., Alpaca) and orchestrates live trade execution with risk management.
  - Sample Output / Side Effects:
    - Prints order confirmations/errors from the broker to console.
    - Logs live trade attempts (including broker response) to logs/trades.log.
    - Connects to external brokerage APIs.
  - Modification Impact / Dependencies:
    - Depends on specific brokerage API libraries (e.g., alpaca-trade-api).
    - Depends on utils/data_structures.py, utils/logger_setup.py, and execution/risk_manager.py.
    - Changes to broker API integrations or trade placement logic directly affect real-money trading.

--- live_signals/ ---
This directory contains the real-time monitoring dashboard.

- File: live_signals/dashboard.py
  - Purpose: Web-based real-time monitoring dashboard built using Streamlit. Provides a comprehensive view of live portfolio, logs, strategy performance, AI insights, and configuration.
  - Sample Output / Side Effects:
    - Launches an interactive web interface in your default browser.
    - Displays live portfolio data, log entries, backtest reports (metrics/plots), and model details.
    - Fetches live data from Alpaca API periodically.
  - Modification Impact / Dependencies:
    - Depends on streamlit, pandas, matplotlib, json, pathlib, datetime.
    - Relies on utils/config_loader.py, execution/live_integration.py (for AlpacaAdapter), data/data_storage.py, ai_models/model_registry.py, backtest/analytics.py.
    - Changes to any of these underlying data sources or their output format will require updates in the dashboard.

--- autotrain/ ---
This directory houses the automated model retraining pipeline.

- File: autotrain/retrainer.py
  - Purpose: Orchestrates the automated ML model retraining pipeline. Checks for retraining triggers (time, performance) and executes the full data fetching, processing, feature engineering, and model training/saving workflow.
  - Sample Output / Side Effects:
    - Prints retraining progress and summary to console.
    - Triggers the creation of new data files (data/processed/, data/features/) and new model files (ai_models/registry/saved_models/).
    - Logs retraining events to logs/errors.log.
  - Modification Impact / Dependencies:
    - Orchestrates data/api_adapters/yahoo_finance_adapter.py, data/data_processor.py, data/data_storage.py, ai_models/feature_engineering.py, ai_models/model_trainer.py, ai_models/model_registry.py.
    - Changes to the retraining logic or integrated pipeline components impact how models are updated over time.

--- utils/ ---
This directory contains core, shared utility functions used across the entire system.

- File: utils/config_loader.py
  - Purpose: Loads application configuration from config.yaml and .env files. Provides a single, cached configuration object accessible globally.
  - Sample Output / Side Effects:
    - Prints config loading messages to console.
    - Returns a dictionary object containing the parsed configuration.
    - Logs errors to logs/errors.log for malformed files or missing environment variables.
  - Modification Impact / Dependencies:
    - Depends on PyYAML and python-dotenv.
    - High Impact: Used by almost every other module to get configuration (e.g., api_keys, strategy params).
    - Changes to its loading logic, location of config.yaml, or how environment variables are substituted impact the entire system's ability to initialize.

- File: utils/logger_setup.py
  - Purpose: Configures and provides structured (JSON) logging for the entire application. Creates separate log files for signals, trades, and errors with rotation.
  - Sample Output / Side Effects:
    - Creates and writes JSON-formatted log entries to logs/signals.log, logs/trades.log, and logs/errors.log.
    - Prints messages to console during setup/testing.
  - Modification Impact / Dependencies:
    - Depends on Python's built-in logging module, json, and utils/config_loader.py.
    - High Impact: Used by virtually every other module for all logging. Changes to log format or file paths require careful coordination across the entire codebase.

- File: utils/data_structures.py
  - Purpose: Defines memory-efficient dataclasses for core trading entities: Signal, Trade, and Position. Uses __slots__ and frozen=True (where appropriate) for performance and data integrity.
  - Sample Output / Side Effects:
    - Returns instances of Signal, Trade, Position.
    - Prints memory test results on direct execution.
  - Modification Impact / Dependencies:
    - Depends on Python's dataclasses module.
    - Used by strategies/base_strategy.py, execution/paper_trader.py, execution/live_integration.py.
    - High Impact: Changes to these dataclasses (e.g., adding/removing fields, changing types) require updates in any module that creates or consumes instances of these objects.

--- logs/ ---
This directory serves as the centralized location for all application logs.

- File: logs/signals.log
  - Purpose: Stores structured JSON logs of all trading signals generated by strategies.
  - Sample Output / Side Effects:
    - Contains a stream of JSON objects, each representing a BUY, SELL, or HOLD signal with its context (timestamp, symbol, strategy, price, confidence).
  - Modification Impact / Dependencies:
    - Written to by strategies/base_strategy.py via utils/logger_setup.py.
    - Read by live_signals/dashboard.py for display.
    - Modifications to its format directly impact base_strategy.py and dashboard.py.

- File: logs/trades.log
  - Purpose: Stores structured JSON logs of all executed trades (both simulated paper trades and live trades).
  - Sample Output / Side Effects:
    - Contains a stream of JSON objects, each representing a trade execution with details like action (BUY/SELL), quantity, price, and associated costs/confirmations.
  - Modification Impact / Dependencies:
    - Written to by execution/paper_trader.py and execution/live_integration.py via utils/logger_setup.py.
    - Read by live_signals/dashboard.py for display.
    - Modifications to its format directly impact paper_trader.py, live_integration.py, and dashboard.py.

- File: logs/errors.log
  - Purpose: Stores structured JSON logs of all warnings, errors, and critical events occurring within the application.
  - Sample Output / Side Effects:
    - Contains a stream of JSON objects, each representing an error, warning, or critical event, often with stack traces and additional context.
  - Modification Impact / Dependencies:
    - Written to by many modules (e.g., data/api_adapters/, data/data_processor.py, execution/risk_manager.py, autotrain/retrainer.py) via utils/logger_setup.py.
    - Read by live_signals/dashboard.py for display.
    - Modifications to its format primarily impact dashboard.py.

--------------------------------------------------------------------------------

6. FUTURE ENHANCEMENTS

This project provides a robust foundation. Here are some potential areas for future enhancement:

- More Data Sources: Integrate APIs like TwelveData, OANDA for broader instrument coverage.
- Advanced Data Processing: Implement tick data processing, order book depth analysis.
- Strategy Refinements:
  - Implement more complex classic (e.g., custom indicators) and quantitative strategies (e.g., statistical arbitrage, pairs trading).
  - Introduce dynamic stop-loss/take-profit mechanisms within strategies.
- AI/ML Evolution:
  - Experiment with deep learning models (LSTM, Transformers) for price prediction (TensorFlow Lite for resource efficiency).
  - Incorporate Reinforcement Learning for dynamic strategy optimization.
  - Add sentiment analysis from news or social media as a feature.
- Advanced Backtesting:
  - Add multi-symbol backtesting and portfolio optimization.
  - Implement variable commission/slippage models based on volume or instrument.
- Execution & Risk:
  - Implement advanced order types (e.g., OCO, trailing stops).
  - Connect to more brokerage APIs (Binance, Interactive Brokers).
  - Develop more sophisticated capital allocation and portfolio rebalancing strategies.
- Live Operations:
  - Implement a true event-driven architecture for real-time market data ingestion and signal processing.
  - Add push notifications (Telegram, Slack) for critical events.
  - Containerize the application (Docker) for easier deployment.
- Dashboard & Monitoring:
  - Integrate real-time charting libraries (e.g., Plotly).
  - Add more granular performance metrics and historical performance comparisons.
  - Implement alert management for critical system statuses.

--------------------------------------------------------------------------------

7. CONTRIBUTING

Contributions are welcome! If you have suggestions or improvements, please feel free to fork the repository, make your changes, and submit a pull request.

--------------------------------------------------------------------------------

8. LICENSE

[Placeholder for License Information]

```                  