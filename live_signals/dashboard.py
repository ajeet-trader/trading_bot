import streamlit as st
import pandas as pd
import time
from datetime import datetime
from pathlib import Path
import json
import os
import io
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
# Adjust sys.path to allow imports from the project root
import sys
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
# Import core components
from utils.config_loader import config
from utils.logger_setup import get_logger # For internal dashboard logging if needed
from execution.live_integration import AlpacaAdapter # For live portfolio data
from data.data_storage import DataStorage # For loading processed data
from ai_models.model_registry import ModelRegistry # For AI model insights
from backtest.analytics import Analytics # To calculate metrics/plots for backtest reports
# Global logger for dashboard itself (optional, mostly for debugging dashboard issues)
dashboard_logger = get_logger("error")
# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="Sapiens AI Trading Bot",
    layout="wide",
    initial_sidebar_state="expanded"
)
# --- Session State Initialization ---
# This ensures data persists across reruns and allows for updates
if "last_refresh_time" not in st.session_state:
    st.session_state.last_refresh_time = datetime.now()
if "portfolio_data" not in st.session_state:
    st.session_state.portfolio_data = {}
if "log_lines" not in st.session_state:
    st.session_state.log_lines = {}
for log_type in ['signals', 'trades', 'errors']:
    if log_type not in st.session_state.log_lines:
        st.session_state.log_lines[log_type] = []
# --- Utility Functions ---
@st.cache_data(ttl=15) # Cache live data for 15 seconds
def get_live_portfolio_data():
    """Fetches live portfolio data from Alpaca."""
    try:
        # Load API keys from config
        api_key = config['api_keys']['alpaca_api_key']
        api_secret = config['api_keys']['alpaca_api_secret']
        
        if not api_key or api_key == "YOUR_ALPACCA_API_KEY_ID_HERE":
            st.warning("Alpaca API keys are not configured. Live data cannot be fetched.")
            return {}
        adapter = AlpacaAdapter(api_key=api_key, api_secret=api_secret, paper=True)
        account_info = adapter.get_account_balance()
        positions = adapter.get_open_positions()
        # Format positions for display
        formatted_positions = []
        for pos in positions:
            formatted_positions.append({
                'symbol': pos.get('symbol'),
                'qty': float(pos.get('qty')),
                'market_value': float(pos.get('market_value')),
                'unrealized_pl': float(pos.get('unrealized_pl')),
                'unrealized_plpc': float(pos.get('unrealized_plpc')) * 100 # Convert to percentage
            })
        return {
            'equity': float(account_info.get('equity', 0)),
            'cash': float(account_info.get('cash', 0)),
            'buying_power': float(account_info.get('buying_power', 0)),
            'positions': formatted_positions,
            'last_fetched': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        dashboard_logger.error(f"Error fetching live portfolio data: {e}", exc_info=True)
        st.error(f"Failed to fetch live data: {e}")
        return {}
def tail_log_file(log_file_path: Path, n_lines: int = 50):
    """Reads the last n_lines from a log file."""
    if not log_file_path.exists():
        return []
    with open(log_file_path, 'r') as f:
        return f.readlines()[-n_lines:]
@st.cache_data # Cache backtest results (they are static after a run)
def get_backtest_reports():
    """Reads all backtest result CSVs and their metadata."""
    results_path = project_root / "backtest" / "results"
    reports = {}
    if not results_path.exists():
        return reports
    
    csv_files = list(results_path.glob('*.csv'))
    for file in csv_files:
        try:
            # We assume the naming convention: {strategy_name}_{symbol}_{interval}.csv
            parts = file.stem.split('_')
            if len(parts) >= 3:
                strategy_name = "_".join(parts[:-2]) # Handle strategy names with underscores
                symbol = parts[-2]
                interval = parts[-1]
                report_key = f"{strategy_name} - {symbol} ({interval})"
                reports[report_key] = file
        except Exception as e:
            dashboard_logger.warning(f"Could not parse backtest report filename {file.name}: {e}")
            continue
    return reports
@st.cache_data # Cache model insights (static after training)
def get_model_insights():
    """Reads metadata for all trained models from the registry."""
    registry = ModelRegistry()
    saved_models_path = registry.registry_path # This is ai_models/saved_models
    
    insights = {}
    if not saved_models_path.exists():
        return insights
    
    metadata_files = list(saved_models_path.glob('*_metadata.json'))
    for file in metadata_files:
        try:
            with open(file, 'r') as f:
                metadata = json.load(f)
                model_name = metadata.get('model_name', file.stem)
                insights[model_name] = metadata
        except Exception as e:
            dashboard_logger.warning(f"Could not load model metadata from {file.name}: {e}")
            continue
    return insights
# --- Dashboard Sections ---
def render_portfolio_overview():
    st.header("📈 Portfolio Overview")
    
    portfolio = st.session_state.portfolio_data
    if not portfolio:
        st.info("Loading live portfolio data...")
        return
    st.markdown(f"**Last Updated:** `{portfolio.get('last_fetched', 'N/A')}`")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Equity", f"${portfolio.get('equity', 0):,.2f}")
    col2.metric("Cash", f"${portfolio.get('cash', 0):,.2f}")
    col3.metric("Buying Power", f"${portfolio.get('buying_power', 0):,.2f}")
    
    # Calculate Unrealized P&L
    total_unrealized_pl = sum(pos['unrealized_pl'] for pos in portfolio.get('positions', []))
    col4.metric("Unrealized P&L", f"${total_unrealized_pl:,.2f}", 
                delta=f"{total_unrealized_pl / portfolio.get('equity', 1) * 100:.2f}%" if portfolio.get('equity', 1) > 0 else "0.00%")
    st.subheader("Open Positions")
    positions_df = pd.DataFrame(portfolio.get('positions', []))
    if not positions_df.empty:
        st.dataframe(positions_df.set_index('symbol'), use_container_width=True)
    else:
        st.info("No open positions.")
def render_live_signals_activity():
    st.header("🚦 Live Signals & Activity")
    
    st.write("Displays recent trading signals and execution logs.")
    
    log_type_filter = st.selectbox(
        "Select Log Type", 
        ['signals', 'trades', 'errors'], 
        key='log_type_filter'
    )
    
    log_lines = st.session_state.log_lines.get(log_type_filter, [])
    
    if log_lines:
        st.json(log_lines)
    else:
        st.info(f"No recent {log_type_filter} logs to display.")
def render_strategy_performance():
    st.header("📊 Strategy Performance (Backtest Reports)")
    
    reports = get_backtest_reports()
    report_selection = st.selectbox(
        "Select Backtest Report", 
        options=list(reports.keys()), 
        index=0 if reports else None,
        key='backtest_report_selector'
    )
    
    if report_selection:
        report_file_path = reports[report_selection]
        st.subheader(f"Report for: {report_selection}")
        
        try:
            # We can re-run analytics for fresh metric calculation or plot generation
            # Or just load the already saved plots
            analytics_engine = Analytics(report_file_path)
            metrics = analytics_engine.calculate_all_metrics()
            
            # Display metrics
            metrics_df = pd.DataFrame.from_dict(metrics, orient='index', columns=['Value'])
            metrics_df.index = metrics_df.index.str.replace('_', ' ').str.title()
            
            # Format percentages and currencies
            for idx, row in metrics_df.iterrows():
                if any(kw in idx.lower() for kw in ['return', 'drawdown', 'win rate', 'volatility']):
                    metrics_df.loc[idx, 'Value'] = f"{row['Value']:.2%}"
                elif any(kw in idx.lower() for kw in ['capital', 'commission']): # Example, adjust as needed
                    metrics_df.loc[idx, 'Value'] = f"${row['Value']:,.2f}"
                else:
                    metrics_df.loc[idx, 'Value'] = f"{row['Value']:.2f}"
            
            st.dataframe(metrics_df, use_container_width=True)
            
            # Display plots (assuming they are saved as PNGs by Analytics module)
            plot_base_name = report_file_path.stem
            equity_plot_path = report_file_path.parent / f"{plot_base_name}_equity.png"
            drawdown_plot_path = report_file_path.parent / f"{plot_base_name}_drawdown.png"
            if equity_plot_path.exists():
                st.image(str(equity_plot_path), caption="Equity Curve vs. Buy & Hold")
            else:
                st.warning("Equity curve plot not found. Run `backtest/engine.py` to generate.")
            
            if drawdown_plot_path.exists():
                st.image(str(drawdown_plot_path), caption="Drawdown Curve")
            else:
                st.warning("Drawdown curve plot not found. Run `backtest/engine.py` to generate.")
        except Exception as e:
            st.error(f"Error loading report for {report_selection}: {e}")
def render_ai_model_insights():
    st.header("🧠 AI/Model Insights")
    
    model_insights = get_model_insights()
    model_selection = st.selectbox(
        "Select Model", 
        options=list(model_insights.keys()), 
        index=0 if model_insights else None,
        key='ai_model_selector'
    )
    
    if model_selection:
        metadata = model_insights[model_selection]
        st.subheader(f"Details for: {model_selection}")
        
        st.json(metadata) # Display raw metadata for full detail
        
        st.markdown("**Core Metrics:**")
        metrics = metadata.get('metrics', {})
        col1, col2, col3 = st.columns(3)
        col1.metric("Accuracy", f"{metrics.get('accuracy', 0):.2%}")
        col2.metric("Precision", f"{metrics.get('precision', 0):.2%}")
        col3.metric("Recall", f"{metrics.get('recall', 0):.2%}")
        st.markdown("**Features Used:**")
        features_used = metrics.get('features_used', [])
        st.code(json.dumps(features_used, indent=2))
    else:
        st.info("No trained models found in the registry.")
def render_system_logs():
    st.header("📋 System Logs")
    
    st.write("View detailed logs for signals, trades, and errors.")
    
    log_level_filter = st.radio(
        "Filter by Log Type",
        ['All', 'signals', 'trades', 'errors'],
        index=0,
        horizontal=True,
        key='system_log_level_filter'
    )
    
    search_term = st.text_input("Search Logs", key='log_search_term')
    
    all_logs_combined = []
    for log_type in ['signals', 'trades', 'errors']:
        if log_level_filter == 'All' or log_type == log_level_filter:
            log_path = project_root / "logs" / f"{log_type}.log"
            all_logs_combined.extend(tail_log_file(log_path, 200)) # Get more lines for search
    filtered_logs = []
    for line in reversed(all_logs_combined): # Display newest first
        if search_term.lower() in line.lower():
            filtered_logs.append(line.strip())
            
    if filtered_logs:
        st.text_area("Recent Log Entries", "\n".join(filtered_logs), height=400)
    else:
        st.info("No matching log entries found.")
def render_settings_config():
    st.header("⚙️ Settings & Configuration")
    
    st.info("This section displays the current configuration. To modify, please edit `config.yaml` and restart the bot.")
    
    st.subheader("General Settings")
    st.json(config.get('system', {}))
    st.subheader("Strategy Configurations")
    st.json(config.get('strategies', {}))
    st.subheader("API Key Placeholders (not actual keys)")
    api_keys_masked = {
        key: f"{val[:4]}****{val[-4:]}" if val and len(val) > 8 else "****"
        for key, val in config.get('api_keys', {}).items()
    }
    st.json(api_keys_masked)
    #st.json(config.get('api_keys', {}))
    
    st.subheader("Risk Management Settings")
    st.json(config.get('risk_management', {}))
# --- Main Dashboard Layout ---
def main_dashboard():
    # Sidebar for auto-refresh and navigation
    with st.sidebar:
        st.title("Admin Controls")
        
        refresh_rate_sec = st.slider("Auto-Refresh Interval (seconds)", 5, 60, 15)
        st.session_state.refresh_rate = refresh_rate_sec
        if st.button("Manual Refresh"):
            st.session_state.last_refresh_time = datetime.now()
            #st.experimental_rerun()
            st.rerun()

        
        st.write(f"Last auto-refresh: {st.session_state.last_refresh_time.strftime('%H:%M:%S')}")
        
        st.markdown("---")
        st.markdown("### Navigation")
        
    # --- Main Content Area ---
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "💰 Portfolio Overview", 
        "🚦 Live Activity", 
        "📊 Strategy Performance", 
        "🧠 AI Insights", 
        "📋 System Logs", 
        "⚙️ Configuration"
    ])
    # --- Update Live Data ---
    # This block will run on every refresh/rerun
    st.session_state.portfolio_data = get_live_portfolio_data()
    st.session_state.log_lines['signals'] = tail_log_file(project_root / "logs" / "signals.log", n_lines=50)
    st.session_state.log_lines['trades'] = tail_log_file(project_root / "logs" / "trades.log", n_lines=50)
    st.session_state.log_lines['errors'] = tail_log_file(project_root / "logs" / "errors.log", n_lines=50)
    with tab1:
        render_portfolio_overview()
    with tab2:
        render_live_signals_activity()
    with tab3:
        render_strategy_performance()
    with tab4:
        render_ai_model_insights()
    with tab5:
        render_system_logs()
    with tab6:
        render_settings_config()
    # --- Auto-refresh logic ---
    time_since_last_refresh = (datetime.now() - st.session_state.last_refresh_time).total_seconds()
    if time_since_last_refresh >= st.session_state.refresh_rate:
        st.session_state.last_refresh_time = datetime.now()
        #st.experimental_rerun()
        st.rerun()
# --- Entry point for Streamlit ---
if __name__ == "__main__":
    main_dashboard()