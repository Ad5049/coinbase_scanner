import os
import requests
from datetime import datetime

# Configuration
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
PAIRS = ["BTC-USD", "ETH-USD", "SOL-USD", "AVAX-USD", "DOGE-USD", "LINK-USD"]
MIN_24H_CHANGE = 0.50  # %
TAKE_PROFIT_PCT = 3.0   # %

def send_discord_alerts(message):
    if not DISCORD_WEBHOOK_URL:
        print("Discord webhook URL not set.")
        return
    payload = {"content": message}
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    if response.status_code != 204:
        print(f"Failed to send Discord alert: {response.status_code}, {response.text}")

def scan_markets():
    print(f"[{datetime.now()}] Running Coinbase momentum scan...")
    alerts_sent = 0

    for pair in PAIRS:
        url = f"https://api.exchange.coinbase.com/products/{pair}/stats"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code != 200:
                continue
            data = res.json()
            
            open_price = float(data.get("open", 0))
            last_price = float(data.get("last", 0))
            
            if open_price == 0:
                continue
                
            change_pct = ((last_price - open_price) / open_price) * 100
            
            if change_pct >= MIN_24H_CHANGE:
                target_exit = last_price * (1 + (TAKE_PROFIT_PCT / 100))
                msg = (
                    f"🚨 **Coinbase Momentum Signal Detected** 🚨\n"
                    f"• **Pair**: {pair}\n"
                    f"• **Current Price**: ${last_price:,.4f}\n"
                    f"• **24h Change**: +{change_pct:.2f}%\n"
                    f"• **Target Exit (+{TAKE_PROFIT_PCT}%)**: **${target_exit:,.4f}**\n"
                    f"👉 *Action: Open Coinbase Advanced, buy, and set Limit Sell to ${target_exit:,.4f}*"
                )
                send_discord_alerts(msg)
                alerts_sent += 1
        except Exception as e:
            print(f"Error fetching {pair}: {e}")

    print(f"Scan complete. Sent {alerts_sent} alerts.")

if __name__ == "__main__":
    scan_markets()
    
