import streamlit as st
import pandas as pd
from coinbase.rest import RESTClient

# Page configuration
st.set_page_config(page_title="Coinbase Income Engine", layout="wide")

st.title("🪙 Coinbase Advanced Trade Engine")
st.markdown("**Operational Target:** Spot Momentum & Stablecoin Yield Protection")

def sanitize_private_key(raw_key):
    if not raw_key:
        return ""
    # Replace literal string escaped newlines with real newlines
    cleaned = raw_key.replace("\\n", "\n")
    # Strip headers/footers and all internal whitespace to get pure base64 payload
    body = cleaned.replace("-----BEGIN EC PRIVATE KEY-----", "").replace("-----END EC PRIVATE KEY-----", "").strip()
    body = "".join(body.split())
    if not body:
        return raw_key
    # Rebuild standard PEM block with correct 64-character line wraps
    chunks = [body[i:i+64] for i in range(0, len(body), 64)]
    return f"-----BEGIN EC PRIVATE KEY-----\n" + "\n".join(chunks) + "\n-----END EC PRIVATE KEY-----\n"

# Load credentials safely from Streamlit secrets
default_key = st.secrets["CDP_API_KEY_NAME"] if "CDP_API_KEY_NAME" in st.secrets else ""
raw_secret = st.secrets["CDP_PRIVATE_KEY"] if "CDP_PRIVATE_KEY" in st.secrets else ""
default_secret = sanitize_private_key(raw_secret)

# Sidebar: API Credentials & Parameters
st.sidebar.header("Coinbase Configuration")
api_key_input = st.sidebar.text_input("CDP API Key Name", value=default_key, type="default")
api_secret_input = st.sidebar.text_area("CDP Private Key", value=default_secret)

target_pairs = st.sidebar.multiselect("Active Pairs", ["BTC-USD", "ETH-USD", "SOL-USD", "AVAX-USD"], default=["BTC-USD", "ETH-USD"])
min_momentum = st.sidebar.slider("Min 24h Change Filter (%)", 0.0, 10.0, 2.0, 0.5)

# Account & Holding Status
st.subheader("Wallet Asset Reconciliation")
if api_key_input and api_secret_input:
    try:
        # Sanitize sidebar text area input as well in case it was edited live
        active_secret = sanitize_private_key(api_secret_input)
        client = RESTClient(api_key=api_key_input, api_secret=active_secret)
        accounts_response = client.get_accounts()
        
        accounts_data = []
        if 'accounts' in accounts_response:
            for acc in accounts_response['accounts']:
                balance = float(acc['available_balance']['value'])
                if balance > 0.001:
                    accounts_data.append({
                        "Currency": acc['currency'],
                        "Balance": balance,
                        "Hold Type": acc.get('hold_inclusive', 'N/A')
                    })
        
        if accounts_data:
            acc_df = pd.DataFrame(accounts_data)
            st.dataframe(acc_df, use_container_width=True)
        else:
            st.info("Connected successfully, but no significant non-zero balances found.")
            
    except Exception as e:
        st.error(f"Authentication or connection failed: {e}")
else:
    st.warning("Enter your CDP API credentials in the sidebar or configure Streamlit secrets.")

# Live Market Momentum Scanner
st.subheader("Targeted Spot Opportunities")

if st.button("Scan Market Tickers"):
    try:
        public_client = RESTClient()
        market_rows = []
        
        for pair in target_pairs:
            ticker = public_client.get(f"/api/v3/brokerage/products/{pair}/ticker")
            current_price = float(ticker.get('price', 0.0))
            low_24h = float(ticker.get('low_24h', 0.0))
            high_24h = float(ticker.get('high_24h', 0.0))
            
            pct_change = ((current_price - low_24h) / low_24h) * 100.0 if low_24h > 0 else 0.0
            
            market_rows.append({
                "Product": pair,
                "Price ($)": current_price,
                "24h Low": low_24h,
                "24h High": high_24h,
                "Calculated Spread %": round(pct_change, 2)
            })
            
        scan_df = pd.DataFrame(market_rows)
        filtered_scan = scan_df[scan_df["Calculated Spread %"] >= min_momentum]
        
        if not filtered_scan.empty:
            st.dataframe(filtered_scan, use_container_width=True)
        else:
            st.info("No trading pairs meet the minimum momentum threshold right now.")
            
    except Exception as e:
        st.error(f"Failed to fetch market data: {e}")

# Execution Log
st.subheader("Order Execution Ledger")
if 'crypto_ledger' not in st.session_state:
    st.session_state.crypto_ledger = []

if st.session_state.crypto_ledger:
    st.dataframe(pd.DataFrame(st.session_state.crypto_ledger), use_container_width=True)
else:
    st.write("No trades executed in current session.")
    
