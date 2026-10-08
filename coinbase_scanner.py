import os
import requests
from datetime import datetime

# Configuration from GitHub Secrets
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# Expanded Asset Universe with historical liquidity
PAIRS = [
    "BTC-USD", "ETH-USD", "SOL-USD", "AVAX-USD", "DOGE-USD", "LINK-USD",
    "SUI-USD", "NEAR-USD", "ADA-USD", "RENDER-USD", "FET-USD", "INJ-USD",
    "MATIC-USD", "UNI-USD", "ATOM-USD", "ICP-USD", "APT-USD", "OP-USD", "ARB-USD", "XRP-USD"
]

def send_discord_alert(message):
    if not DISCORD_WEBHOOK_URL:
        print("Discord webhook URL not configured.")
        return
    payload = {"content": message}
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    if response.status_code != 204:
        print(f"Failed to send Discord alert: {response.status_code}, {response.text}")

def scan_macro_trends():
    print(f"[{datetime.now()}] Running Coinbase Macro Trend & Support Scan...")
    alerts_triggered = 0

    for pair in PAIRS:
        # Fetch daily candles (granularity = 86400 seconds = 1 day)
        url = f"https://api.exchange.coinbase.com/products/{pair}/candles?granularity=86400"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code != 200:
                continue
            candles = res.json()
            
            # Ensure we have enough daily data for moving averages (at least 50 days)
            if not candles or len(candles) < 50:
                continue
                
            # Coinbase daily candles format: [time, low, high, open, close, volume]
            # Candles are returned in reverse chronological order (candles[0] is today/latest)
            closes = [float(c[4]) for c in candles]
            lows = [float(c[1]) for c in candles]
            highs = [float(c[2]) for c in candles]
            
            current_price = closes[0]
            
            # Calculate 50-day Simple Moving Average (SMA)
            sma_50 = sum(closes[:50]) / 50.0
            
            # Determine local support (lowest low of the last 14 days)
            recent_support = min(lows[:14])
            
            # Determine local resistance/recent high (highest high of the last 30 days)
            recent_resistance = max(highs[:30])
            
            # Check if price is pulling back near support or moving average (Dip accumulation condition)
            # Condition: Current price is within 3% of the 50 SMA or near recent support structure
            distance_from_sma = ((current_price - sma_50) / sma_50) * 100
            
            if -4.0 <= distance_from_sma <= 2.0:
                # Data-driven target calculation based on historical range volatility
                # Calculates a realistic upside swing target aiming toward recent resistance or a healthy risk-adjusted margin
                target_gain_pct = max(10.0, min(30.0, ((recent_resistance - current_price) / current_price) * 100 * 0.75))
                target_sell_price = current_price * (1 + (target_gain_pct / 100))
                stop_loss_price = recent_support * 0.98  # Risk boundary just below support
                
                msg = (
                    f"📊 **Macro Accumulation Signal** 📊\n"
                    f"• **Asset**: {pair}\n"
                    f"• **Current Buy Zone**: `${current_price:,.4f}`\n"
                    f"• **50-Day Trend Baseline**: `${sma_50:,.4f}`\n"
                    f"• **Calculated Swing Target (+{target_gain_pct:.1f}%)**: **`${target_sell_price:,.4f}`**\n"
                    f"• **Risk Support Floor**: `${stop_loss_price:,.4f}`\n"
                    f"👉 *Action: Open Coinbase, buy spot at `${current_price:,.4f}`, and set Limit Sell to `${target_sell_price:,.4f}`*"
                )
                send_discord_alert(msg)
                alerts_triggered += 1
                
        except Exception as e:
            print(f"Error processing {pair}: {e}")

    print(f"Macro scan complete. Generated {alerts_triggered} actionable position setups.")

if __name__ == "__main__":
    scan_macro_trends()
    
