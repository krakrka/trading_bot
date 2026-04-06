# db_viewer.py
import pandas as pd
import warnings
from data_pipeline.db import get_db_connection

# On ignore les alertes de connexion pour un affichage propre
warnings.filterwarnings("ignore", category=UserWarning)

def view_database():
    conn = get_db_connection()
    
    print("\n" + "="*60)
    print("📊 EXPLORATEUR DE BASE DE DONNÉES - NEXA TRADING")
    print("="*60 + "\n")

    # 1. Liste des Utilisateurs
    print("👤 UTILISATEURS ENREGISTRÉS :")
    try:
        users = pd.read_sql("SELECT id, email, full_name, created_at FROM users", conn)
        if users.empty:
            print("   (Aucun utilisateur trouvé)")
        else:
            print(users.to_string(index=False))
    except Exception as e:
        print(f"   ❌ Erreur table 'users': {e}")

    print("\n" + "-"*40)

    # 2. Derniers Signaux de Trading
    print("🤖 DERNIERS SIGNAUX IA (trades_history) :")
    try:
        trades = pd.read_sql("""
            SELECT timestamp, ticker, direction, entry_price, confidence, status 
            FROM trades_history 
            ORDER BY timestamp DESC LIMIT 10
        """, conn)
        if trades.empty:
            print("   (Aucun signal généré pour le moment)")
        else:
            print(trades.to_string(index=False))
    except Exception as e:
        print(f"   ❌ Erreur table 'trades_history': {e}")

    print("\n" + "-"*40)

    # 3. État du Calendrier Macro
    print("🌍 DERNIERS ÉVÉNEMENTS MACRO (Gemini Context) :")
    try:
        macro = pd.read_sql("""
            SELECT timestamp, event_name, actual, forecast 
            FROM macro_events 
            WHERE actual != '' 
            ORDER BY timestamp DESC LIMIT 5
        """, conn)
        if macro.empty:
            print("   (Aucune news macro avec résultat 'Actual' trouvée)")
        else:
            print(macro.to_string(index=False))
    except Exception as e:
        print(f"   ❌ Erreur table 'macro_events': {e}")

    print("\n" + "-"*40)

    # 4. Statistiques des Prix
    print("📈 RÉSUMÉ DES DONNÉES DE PRIX :")
    try:
        prices = pd.read_sql("""
            SELECT a.ticker, COUNT(p.id) as total_candles, MAX(p.timestamp) as last_update
            FROM assets a
            LEFT JOIN price_data p ON a.asset_id = p.asset_id
            GROUP BY a.ticker
        """, conn)
        print(prices.to_string(index=False))
    except Exception as e:
        print(f"   ❌ Erreur résumé prix: {e}")

    conn.close()
    print("\n" + "="*60)

if __name__ == "__main__":
    view_database()