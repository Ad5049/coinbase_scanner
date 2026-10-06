import streamlit as st
import pandas as pd
import requests

# Page configuration
st.set_page_config(page_title="Coinbase Income Engine", layout="wide")

st.title("🪙 Coinbase Public Spot Scanner & Exit Planner")
st.markdown("**Operational Target:** Automated Entry Signals & Take-Profit Targets for Hands-Off Execution")

# Sidebar Parameters
st.sidebar.header("Scanner & Exit Parameters")
target_pairs = st.sidebar.multiselect("Active Pairs", ["BTC-USD", "ETH-USD", "SOL-USD", "AVAX-USD", "DOGE-USD"], default=["BTC-USD", "ETH-USD", "SOL-USD", "AVAX-USD"])
min_momentum = st.sidebar.slider("Min 24h Change Filter (%)", 0.0, 10.0, 1.5, 0.5)
profit_target_pct = st.sidebar.slider("Automated Take-Profit Target (%)", 1.0, 10.0, 3.0, 0.5)

# Live Market Momentum Scanner
st.subheader("Targeted Spot Opportunities & Exit Targets")

if st.button("Scan Coinbase Markets"):
    try:
        market_rows = []
        headers = {"Accept": "application/json"}
        
        for pair in target_pairs:
            url = f"https://api.exchange.coinbase.com/products/{pair}/stats"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                last_price = float(data.get('last', 0.0))
                open_price = float(data.get('open', 0.0))
                high_price = float(data.get('high', 0.0))
                low_price = float(data.get('low', 0.0))
                
                pct_change = ((last_price - open_price) / open_price) * 100.0 if open_price > 0 else 0.0
                
                # Automatically calculate target exit price based on selected profit %
                target_exit_price = round(last_price * (1.0 + (profit_target_pct / 100.0)), 4)
                
                market_rows.append({
                    "Product": pair,
                    "Current Price ($)": last_price,
                    "24h Change %": round(pct_change, 2),
                    f"Target Exit (+{profit_target_pct}%)": target_exit_price
                })
                
        if market_rows:
            scan_df = pd.DataFrame(market_rows)
            filtered_scan = scan_df[scan_df["24h Change %"] >= min_momentum]
            
            if not filtered_scan.empty:
                st.dataframe(filtered_scan, use_container_width=True)
                st.markdown("👉 **Action Protocol:** When entering a position, immediately set your Coinbase Limit Sell order to the exact **Target Exit** price displayed above, then close the app.")
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
    
