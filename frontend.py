import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import requests
import json
import time

# Page configuration
st.set_page_config(
    page_title="Binance Crypto Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #f0b90b;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #0e1117;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #262730;
    }
    .price-positive {
        color: #00ff00;
        font-weight: bold;
    }
    .price-negative {
        color: #ff4b4b;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

class BinanceAPI:
    def __init__(self):
        self.base_url = "https://api.binance.com/api/v3"
    
    def get_historical_klines(self, symbol="BTCUSDT", interval="1m", limit=500):
        """Fetch historical candlestick data from Binance"""
        url = f"{self.base_url}/klines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Convert to DataFrame
            df = pd.DataFrame(data, columns=[
                "open_time", "open", "high", "low", "close", "volume",
                "close_time", "quote_asset_volume", "trades",
                "taker_buy_base", "taker_buy_quote", "ignore"
            ])
            
            # Convert timestamps and numeric columns
            df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
            df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
            
            numeric_cols = ["open", "high", "low", "close", "volume"]
            df[numeric_cols] = df[numeric_cols].astype(float)
            
            return df
            
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            return pd.DataFrame()
    
    def get_current_price(self, symbol="BTCUSDT"):
        """Get current price for a symbol"""
        url = f"{self.base_url}/ticker/price"
        params = {"symbol": symbol}
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Error fetching current price: {e}")
            return None
    
    def get_24hr_ticker(self, symbol="BTCUSDT"):
        """Get 24hr ticker statistics"""
        url = f"{self.base_url}/ticker/24hr"
        params = {"symbol": symbol}
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Error fetching 24hr stats: {e}")
            return None

def create_candlestick_chart(df, title="BTC/USDT Price Chart"):
    """Create an interactive candlestick chart"""
    fig = go.Figure(data=[
        go.Candlestick(
            x=df['open_time'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name="Price"
        )
    ])
    
    fig.update_layout(
        title=title,
        xaxis_title="Time",
        yaxis_title="Price (USDT)",
        template="plotly_dark",
        height=500,
        xaxis_rangeslider_visible=False
    )
    
    return fig

def create_volume_chart(df):
    """Create volume chart"""
    fig = px.bar(df, x='open_time', y='volume', 
                 title="Trading Volume",
                 labels={'volume': 'Volume', 'open_time': 'Time'})
    
    fig.update_layout(
        template="plotly_dark",
        height=300,
        showlegend=False
    )
    
    return fig

def main():
    # Initialize Binance API
    binance = BinanceAPI()
    
    # Header
    st.markdown('<h1 class="main-header">📈 Binance Crypto Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("Configuration")
    
    # Symbol selection
    symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT"]
    selected_symbol = st.sidebar.selectbox("Select Symbol", symbols, index=0)
    
    # Time interval selection
    intervals = ["1m", "5m", "15m", "1h", "4h", "1d"]
    selected_interval = st.sidebar.selectbox("Select Interval", intervals, index=3)
    
    # Data limit
    data_limit = st.sidebar.slider("Number of Data Points", min_value=100, max_value=1000, value=500, step=100)
    
    # Auto-refresh
    auto_refresh = st.sidebar.checkbox("Auto-refresh (10 seconds)", value=False)
    
    # Main content
    col1, col2, col3, col4 = st.columns(4)
    
    # Fetch current price and 24hr stats
    current_price_data = binance.get_current_price(selected_symbol)
    ticker_24hr = binance.get_24hr_ticker(selected_symbol)
    
    if current_price_data and ticker_24hr:
        current_price = float(current_price_data['price'])
        price_change = float(ticker_24hr['priceChange'])
        price_change_percent = float(ticker_24hr['priceChangePercent'])
        volume = float(ticker_24hr['volume'])
        high_24h = float(ticker_24hr['highPrice'])
        low_24h = float(ticker_24hr['lowPrice'])
        
        with col1:
            st.metric(
                label=f"Current Price ({selected_symbol})",
                value=f"${current_price:,.2f}",
                delta=f"{price_change_percent:.2f}%"
            )
        
        with col2:
            st.metric(
                label="24h Volume",
                value=f"${volume:,.0f}"
            )
        
        with col3:
            st.metric(
                label="24h High",
                value=f"${high_24h:,.2f}"
            )
        
        with col4:
            st.metric(
                label="24h Low",
                value=f"${low_24h:,.2f}"
            )
    
    # Fetch and display historical data
    st.subheader(f"Price Chart - {selected_symbol}")
    
    with st.spinner("Fetching market data..."):
        df = binance.get_historical_klines(
            symbol=selected_symbol,
            interval=selected_interval,
            limit=data_limit
        )
    
    if not df.empty:
        # Create tabs for different visualizations
        tab1, tab2, tab3, tab4 = st.tabs(["Candlestick Chart", "Price Analysis", "Volume Analysis", "Raw Data"])
        
        with tab1:
            fig_candle = create_candlestick_chart(df, f"{selected_symbol} Price Chart ({selected_interval})")
            st.plotly_chart(fig_candle, use_container_width=True)
        
        with tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                # Price trend line
                fig_line = px.line(df, x='open_time', y='close', 
                                 title=f"{selected_symbol} Price Trend",
                                 labels={'close': 'Price (USDT)', 'open_time': 'Time'})
                fig_line.update_layout(template="plotly_dark", height=400)
                st.plotly_chart(fig_line, use_container_width=True)
            
            with col2:
                # Price statistics
                st.subheader("Price Statistics")
                stats_data = {
                    'Metric': ['Current Price', '24h Change', '24h Change %', '24h High', '24h Low', '24h Volume'],
                    'Value': [
                        f"${current_price:,.2f}" if current_price_data else "N/A",
                        f"${price_change:,.2f}" if ticker_24hr else "N/A",
                        f"{price_change_percent:.2f}%" if ticker_24hr else "N/A",
                        f"${high_24h:,.2f}" if ticker_24hr else "N/A",
                        f"${low_24h:,.2f}" if ticker_24hr else "N/A",
                        f"${volume:,.0f}" if ticker_24hr else "N/A"
                    ]
                }
                stats_df = pd.DataFrame(stats_data)
                st.dataframe(stats_df, use_container_width=True, hide_index=True)
        
        with tab3:
            fig_volume = create_volume_chart(df)
            st.plotly_chart(fig_volume, use_container_width=True)
            
            # Volume statistics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Average Volume", f"${df['volume'].mean():.2f}")
            with col2:
                st.metric("Max Volume", f"${df['volume'].max():.2f}")
        
        with tab4:
            st.subheader("Raw Market Data")
            st.dataframe(df.tail(20), use_container_width=True)
            
            # Data summary
            st.subheader("Data Summary")
            summary_col1, summary_col2, summary_col3 = st.columns(3)
            
            with summary_col1:
                st.metric("Total Records", len(df))
                st.metric("Date Range", f"{df['open_time'].min().strftime('%Y-%m-%d')} to {df['open_time'].max().strftime('%Y-%m-%d')}")
            
            with summary_col2:
                st.metric("Average Price", f"${df['close'].mean():.2f}")
                st.metric("Price Std Dev", f"${df['close'].std():.2f}")
            
            with summary_col3:
                st.metric("Min Price", f"${df['low'].min():.2f}")
                st.metric("Max Price", f"${df['high'].max():.2f}")
    
    else:
        st.error("No data available. Please check your connection or try a different symbol.")
    
    # Auto-refresh functionality
    if auto_refresh:
        time.sleep(10)
        st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "**Note**: This dashboard displays real-time cryptocurrency data from Binance API. "
        "Data may be delayed and should not be used for trading decisions."
    )

if __name__ == "__main__":
    main()