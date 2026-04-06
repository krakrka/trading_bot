# execution/broker_manager.py

import MetaTrader5 as mt5
from pybit.unified_trading import HTTP
import os

# --- CONFIGURATION BYBIT ---
session_bybit = HTTP(
    testnet=True, # True pour compte DEMO
    api_key=os.getenv("BYBIT_API_KEY"),
    api_secret=os.getenv("BYBIT_API_SECRET"),
)

def execute_bybit_trade(ticker, direction, qty, sl, tp):
    """Envoie un ordre au broker Bybit (Crypto)."""
    try:
        side = "Buy" if direction == "ACHAT" else "Sell"
        # Formatage du ticker pour Bybit (ex: BTCUSD -> BTCUSDT)
        symbol = ticker.replace("USD", "USDT")
        
        order = session_bybit.place_order(
            category="linear",
            symbol=symbol,
            side=side,
            orderType="Market",
            qty=qty,
            stopLoss=str(sl),
            takeProfit=str(tp),
        )
        print(f"✅ BYBIT : Ordre {side} placé sur {symbol}")
        return order
    except Exception as e:
        print(f"❌ Erreur BYBIT : {e}")

def execute_mt5_trade(ticker, direction, volume, sl, tp):
    """Envoie un ordre à MetaTrader 5 (Indices/Forex)."""
    if not mt5.initialize():
        print("❌ MT5 : Échec de l'initialisation")
        return

    symbol = "NAS100" if "USTEC" in ticker else ticker # Adaptation selon le broker
    type_trade = mt5.ORDER_TYPE_BUY if direction == "ACHAT" else mt5.ORDER_TYPE_SELL
    price = mt5.symbol_info_tick(symbol).ask if direction == "ACHAT" else mt5.symbol_info_tick(symbol).bid

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": float(volume),
        "type": type_trade,
        "price": price,
        "sl": float(sl),
        "tp": float(tp),
        "magic": 123456, # ID unique de ton bot
        "comment": "Nexa AI Signal",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"❌ MT5 : Échec de l'ordre ({result.retcode})")
    else:
        print(f"✅ MT5 : Ordre {direction} exécuté sur {symbol}")
    
    mt5.shutdown()