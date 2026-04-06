# execution/bot_daemon.py
import time
import random
import requests
import ccxt
from data_pipeline.db import get_db_connection

def get_real_market_price(ticker):
    """Va chercher le vrai prix en direct sur le marché"""
    try:
        if ticker == "NAS100":
            # Simulation pour le Nasdaq (en attendant l'intégration MT5)
            return round(20500.00 + random.uniform(-15, 15), 2)
        else:
            # Prix réel via l'API publique de Binance
            symbol = ticker.replace("/", "")
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
            response = requests.get(url)
            return round(float(response.json()['price']), 2)
    except Exception as e:
        print(f"⚠️ Erreur de prix sur {ticker} : {e}")
        return 100.00

def get_broker_keys():
    """Va chercher la DERNIÈRE clé API Bybit et la nettoie"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # On prend la ligne la plus récente avec "ORDER BY id DESC"
        cur.execute("SELECT api_key, api_secret FROM broker_accounts WHERE broker_name LIKE 'BYBIT%' ORDER BY id DESC LIMIT 1")
        keys = cur.fetchone()
        conn.close()
        
        if keys:
            # Nettoyage des éventuels espaces invisibles copiés par erreur
            key = keys[0].strip()
            secret = keys[1].strip()
            
            # Message de debug pour vérifier que c'est bien ta clé
            print(f"🔑 [DEBUG] Clé Bybit détectée en base de données : {key[:4]}...{key[-4:]}")
            return key, secret
            
        return None, None
    except Exception as e:
        print(f"Erreur lecture clés : {e}")
        return None, None

def execute_bybit_order(api_key, api_secret, ticker, direction):
    """Envoie le vrai signal au serveur Bybit en Live"""
    try:
        exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot' # Force le trading sur le portefeuille Spot
            }
        })
        
        # ⚠️ LE SANDBOX EST DÉSACTIVÉ : EXÉCUTION EN ARGENT RÉEL ⚠️
        # exchange.set_sandbox_mode(True) 

        symbol = ticker
        order_type = 'market' 
        side = 'buy' if direction == "ACHAT" else 'sell'
        
        # Quantité ajustée (ATTENTION : utilise de petites quantités pour tester)
        amount = 0.1 if "SOL" in ticker else 0.001 

        print(f"🚀 ENVOI DE L'ORDRE {side.upper()} DE {amount} SUR {symbol} CHEZ BYBIT (LIVE)...")
        order = exchange.create_order(symbol, order_type, side, amount)
        
        print(f"✅ ORDRE EXÉCUTÉ SUR BYBIT ! ID: {order['id']}")
        return True

    except Exception as e:
        print(f"❌ Bybit a refusé l'ordre : {e}")
        return False

def run_bot():
    print("\n" + "="*50)
    print("🚀 DÉMARRAGE DU MOTEUR IA & EXÉCUTION RÉELLE (LIVE) 🚀")
    print("="*50)
    
    while True:
        print("\n📡 Analyse des marchés en cours...")
        time.sleep(3)
        
        # Sélection aléatoire pour le test de l'architecture
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
            # Exécution réelle chez Bybit
            success = execute_bybit_order(api_key, api_secret, ticker, direction)
            if not success:
                status = 'FAILED'
        else:
            print("⚠️ Aucune clé API trouvée. Mode Virtual (Paper Trading) activé.")
            status = 'VIRTUAL'

        # --- 2. ENREGISTREMENT DANS LA BASE DE DONNÉES (DASHBOARD) ---
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
            cur.close()
            conn.close()
            print("💾 Sauvegarde en base de données : succès. Le dashboard se met à jour.")
        except Exception as e:
            print(f"❌ Erreur de sauvegarde en base de données : {e}")
        
        print("⏳ Attente du prochain cycle (15 secondes)...")
        time.sleep(15)

if __name__ == "__main__":
    run_bot()