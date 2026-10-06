import streamlit as st
import pandas as pd
import requests

# Page configuration
st.set_page_config(page_title="Coinbase Income Engine", layout="wide")

st.title("🪙 Coinbase Public Spot Scanner")
st.markdown("**Operational Target:** Real-Time Momentum & Spread Discovery (No Auth Hassles)")

# Sidebar Parameters
st.sidebar.header("Scanner Configuration")
target_pairs = st.sidebar.multiselect("Active Pairs", ["BTC-USD", "ETH-USD", "SOL-USD", "AVAX-USD", "DOGE-USD"], default=["BTC-USD", "ETH-USD", "SOL-USD"])
min_momentum = st.sidebar.slider("Min 24h Change Filter (%)", 0.0, 10.0, 1.5, 0.5)

# Live Market Momentum Scanner
st.subheader("Targeted Spot Opportunities")

if st.button("Scan Coinbase Markets"):
    try:
        market_rows = []
        headers = {"Accept": "application/json"}
        
        for pair in target_pairs:
            # Use public Coinbase Exchange API endpoint
            url = f"https://api.exchange.coinbase.com/products/{pair}/stats"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                last_price = float(data.get('last', 0.0))
                open_price = float(data.get('open', 0.0))
                high_price = float(data.get('high', 0.0))
                low_price = float(data.get('low', 0.0))
                
                # Calculate 24h price change percentage
                pct_change = ((last_price - open_price) / open_price) * 100.0 if open_price > 0 else 0.0
                
                market_rows.append({
                    "Product": pair,
                    "Last Price ($)": last_price,
                    "24h Open": open_price,
                    "24h High": high_price,
                    "24h Low": low_price,
                    "Change %": round(pct_change, 2)
                })
                
        if market_rows:
            scan_df = pd.DataFrame(market_rows)
            filtered_scan = scan_df[scan_df["Change %"] >= min_momentum]
            
            if not filtered_scan.empty:
                st.dataframe(filtered_scan, use_container_width=True)
            else:
                st.info("Scanner active. No trading pairs currently meet the selected minimum momentum threshold.")
        else:
            st.error("Failed to retrieve market statistics from Coinbase public endpoints.")
            
    except Exception as e:
        st.error(f"Market scan error: {e}")

# Execution Log
st.subheader("Order Execution Ledger")
if 'crypto_ledger' not in st.session_state:
    st.session_state.crypto_ledger = []

if st.session_state.crypto_ledger:
    st.dataframe(pd.DataFrame(st.session_state.crypto_ledger), use_container_width=True)
else:
    st.write("No manual trades logged in current session.")
    
