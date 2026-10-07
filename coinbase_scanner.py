import os
import requests
from datetime import datetime

# Configuration
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# Expanded list of liquid pairs
PAIRS = [
    "BTC-USD", "ETH-USD", "SOL-USD", "AVAX-USD", "DOGE-USD", "LINK-USD",
    "SUI-USD", "NEAR-USD", "ADA-USD", "RENDER-USD", "FET-USD", "INJ-USD"
]

# Using 1-hour candle momentum for frequent, high-probability intraday setups
MIN_1H_CHANGE = 0.40  # % minimum threshold within the last hour

def send_discord_alerts(message):
    if not DISCORD_WEBHOOK_URL:
        print("Discord webhook URL not set.")
        return
    payload = {"content": message}
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    if response.status_code != 204:
        print(f"Failed to send Discord alert: {response.status_code}, {response.text}")

def scan_markets():
    print(f"[{datetime.now()}] Running Coinbase 1-hour momentum scan...")
    alerts_sent = 0

    for pair in PAIRS:
        # Fetch 1-hour granularity candles from Coinbase Exchange API (granularity = 3600 seconds)
        url = f"https://api.exchange.coinbase.com/products/{pair}/candles?granularity=3600"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code != 200:
                continue
            candles = res.json()
            
            if not candles or len(candles) < 2:
                continue
                
            # Coinbase candles format: [time, low, high, open, close, volume]
            # candles[0] is the current/most recent incomplete/completed 1h candle
            current_open = float(candles[0][3])
            current_close = float(candles[0][4])
            
            if current_open == 0:
                continue
                
            change_pct = ((current_close - current_open) / current_open) * 100
            
            if change_pct >= MIN_1H_CHANGE:
                dynamic_tp_pct = max(2.0, min(6.0, change_pct * 0.6))
                target_exit = current_close * (1 + (dynamic_tp_pct / 100))
                
                msg = (
                    f"🚨 **Coinbase 1H Momentum Signal** 🚨\n"
                    f"• **Pair**: {pair}\n"
                    f"• **Current Price**: ${current_close:,.4f}\n"
                    f"• **1H Change**: +{change_pct:.2f}%\n"
                    f"• **Dynamic Target (+{dynamic_tp_pct:.1f}%)**: **${target_exit:,.4f}**\n"
                    f"👉 *Action: Open Coinbase Advanced, buy, and set Limit Sell to ${target_exit:,.4f}*"
                )
                send_discord_alerts(msg)
                alerts_sent += 1
        except Exception as e:
            print(f"Error fetching {pair}: {e}")

    print(f"Scan complete. Sent {alerts_sent} alerts.")

if __name__ == "__main__":
    scan_markets()
    
