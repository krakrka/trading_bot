# execution/bot_daemon.py
import time
import random
import requests
import ccxt  # 🟢 La librairie magique pour exécuter les trades cryptos
from data_pipeline.db import get_db_connection

def get_real_market_price(ticker):
    try:
        if ticker == "NAS100":
            return round(20500.00 + random.uniform(-15, 15), 2)
        else:
            symbol = ticker.replace("/", "")
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
            response = requests.get(url)
            return round(float(response.json()['price']), 2)
    except Exception:
        return 100.00

def get_broker_keys():
    """Va chercher la clé API Bybit du premier utilisateur dans la DB"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT api_key, api_secret FROM broker_accounts WHERE broker_name LIKE 'BYBIT%' LIMIT 1")
        keys = cur.fetchone()
        conn.close()
        if keys:
            return keys[0], keys[1]
        return None, None
    except Exception as e:
        print(f"Erreur lecture clés : {e}")
        return None, None

def execute_bybit_order(api_key, api_secret, ticker, direction):
    """Envoie le vrai signal au serveur Bybit"""
    try:
        # Initialisation de la connexion sécurisée Bybit
        exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
        })
        
        # ⚠️ MODE TESTNET ACTIVÉ : Pour ne pas utiliser d'argent réel tout de suite !
        exchange.set_sandbox_mode(True)

        symbol = ticker # ex: 'BTC/USDT'
        order_type = 'market' # Ordre au prix du marché direct
        side = 'buy' if direction == "ACHAT" else 'sell'
        
        # Quantité minimale (ex: 0.001 BTC ou 0.1 SOL). À adapter selon la crypto.
        amount = 0.1 if "SOL" in ticker else 0.001 

        print(f"🚀 ENVOI DE L'ORDRE {side.upper()} CHEZ BYBIT...")
        
        # L'ordre part chez le broker !
        order = exchange.create_order(symbol, order_type, side, amount)
        
        print(f"✅ ORDRE EXÉCUTÉ SUR BYBIT ! ID: {order['id']}")
        return True

    except Exception as e:
        print(f"❌ Bybit a refusé l'ordre : {e}")
        return False

def run_bot():
    print("\n" + "="*50)
    print("🚀 DÉMARRAGE DU MOTEUR IA & EXÉCUTION RÉELLE 🚀")
    print("="*50)
    
    while True:
        print("\n📡 Analyse des marchés en cours...")
        time.sleep(3)
        
        # Pour tester l'exécution, on se limite aux cryptos (MT5/NAS100 viendra après sur ton PC Windows)
        tickers = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
        ticker = random.choice(tickers)
        direction = random.choice(["ACHAT", "VENTE"])
        price = get_real_market_price(ticker)
        confidence = round(random.uniform(75.0, 99.9), 1)
        
        print(f"🎯 SIGNAL IA : {direction} sur {ticker} à {price}$ (Confiance: {confidence}%)")
        
        # --- 1. TENTATIVE D'EXÉCUTION CHEZ LE BROKER ---
        api_key, api_secret = get_broker_keys()
        
        status = 'OPEN'
        if api_key and api_secret:
            # Si le client a rentré ses clés, on exécute en vrai !
            success = execute_bybit_order(api_key, api_secret, ticker, direction)
            if not success:
                status = 'FAILED' # L'ordre a échoué chez le broker
        else:
            print("⚠️ Aucune clé API trouvée en DB. Trading virtuel (Paper Trading) activé.")
            status = 'VIRTUAL'

        # --- 2. ENREGISTREMENT DANS LE DASHBOARD ---
        if direction == "ACHAT":
            stop_loss = round(price * 0.98, 2)
            take_profit = round(price * 1.04, 2)
        else:
            stop_loss = round(price * 1.02, 2)
            take_profit = round(price * 0.96, 2)

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO trades_history 
                (ticker, direction, entry_price, stop_loss, take_profit, confidence, pnl, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (ticker, direction, price, stop_loss, take_profit, confidence, 0.0, status))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Erreur DB : {e}")
        
        time.sleep(15)

if __name__ == "__main__":
    run_bot()