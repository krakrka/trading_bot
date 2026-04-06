# execution/bot_daemon.py
import time
import pandas as pd
from data_pipeline.db import get_db_connection
from execution.broker_manager import execute_bybit_trade, execute_mt5_trade
# Importe ton modèle d'inférence ici
# from model_trainer import predict_signal 

def fetch_active_accounts():
    """Récupère tous les comptes API configurés par les utilisateurs."""
    conn = get_db_connection()
    query = "SELECT user_id, broker_name, api_key, api_secret FROM broker_accounts"
    accounts = pd.read_sql(query, conn)
    conn.close()
    return accounts

def scan_and_execute():
    print("🚀 Nexa AI Bot Daemon démarré...")
    
    while True:
        try:
            # 1. Récupérer les comptes configurés
            accounts = fetch_active_accounts()
            if accounts.empty:
                print("⏳ En attente de configuration de comptes API par les utilisateurs...")
                time.sleep(30)
                continue

            # 2. Simulation d'un signal IA (À remplacer par ton script d'inférence)
            # On imagine un signal sur le NAS100
            signal = {
                "ticker": "NAS100",
                "direction": "ACHAT",
                "price": 18250.50,
                "sl": 18100.00,
                "tp": 18500.00,
                "confidence": 0.85
            }

            # 3. Boucler sur chaque compte pour exécuter le trade
            for _, acc in accounts.iterrows():
                print(f"🔄 Traitement pour l'utilisateur {acc['user_id']} sur {acc['broker_name']}")
                
                if "BYBIT" in acc['broker_name'].upper():
                    execute_bybit_trade(
                        ticker=signal['ticker'],
                        direction=signal['direction'],
                        qty=0.01, # À calculer selon le risk management
                        sl=signal['sl'],
                        tp=signal['tp'],
                        api_key=acc['api_key'],
                        api_secret=acc['api_secret']
                    )
                
                elif "MT5" in acc['broker_name'].upper():
                    # Rappel: MT5 nécessite Windows ou un Bridge
                    execute_mt5_trade(
                        ticker=signal['ticker'],
                        direction=signal['direction'],
                        volume=0.1,
                        sl=signal['sl'],
                        tp=signal['tp']
                    )

            # Logique de sauvegarde du trade en base de données pour le dashboard
            save_trade_to_db(signal)

        except Exception as e:
            print(f"❌ Erreur Daemon : {e}")
        
        time.sleep(60) # Scan toutes les minutes

def save_trade_to_db(signal):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO trades_history (ticker, direction, entry_price, confidence, status)
        VALUES (%s, %s, %s, %s, %s)
    """, (signal['ticker'], signal['direction'], signal['price'], signal['confidence'], 'OPEN'))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    scan_and_execute()