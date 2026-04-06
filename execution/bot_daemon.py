# bot_daemon.py
import time
import random
from data_pipeline.db import get_db_connection

def run_bot():
    print("\n" + "="*50)
    print("🚀 DÉMARRAGE DU MOTEUR IA NEXA TRADING 🚀")
    print("="*50)
    
    while True:
        print("\n📡 Analyse des marchés en cours (Machine Learning)...")
        time.sleep(3) # Simule le temps de calcul de l'IA
        
        # Génération d'un signal de trading
        tickers = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "NAS100"]
        directions = ["ACHAT", "VENTE"]
        
        ticker = random.choice(tickers)
        direction = random.choice(directions)
        price = round(random.uniform(150, 68000), 2)
        confidence = round(random.uniform(75.0, 99.9), 1)
        
        print(f"🎯 SIGNAL DÉTECTÉ : {direction} sur {ticker} à {price}$ (Confiance: {confidence}%)")
        
        # Envoi du signal dans ta base de données Neon
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Création de la table trades_history au cas où elle n'existerait pas
            cur.execute("""
                CREATE TABLE IF NOT EXISTS trades_history (
                    id SERIAL PRIMARY KEY,
                    ticker VARCHAR(20),
                    direction VARCHAR(10),
                    entry_price DECIMAL,
                    confidence DECIMAL,
                    status VARCHAR(20),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            cur.execute("""
                INSERT INTO trades_history (ticker, direction, entry_price, confidence, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (ticker, direction, price, confidence, 'OPEN'))
            
            conn.commit()
            cur.close()
            conn.close()
            print("✅ Ordre enregistré dans Neon. Le Dashboard cloud va s'actualiser !")
            
        except Exception as e:
            print(f"❌ Erreur base de données : {e}")
        
        print("⏳ Attente du prochain cycle (15 secondes)...")
        time.sleep(15)

if __name__ == "__main__":
    run_bot()