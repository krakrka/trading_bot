# reset_db.py
from data_pipeline.db import get_db_connection, init_database

def full_reset():
    print("⚠️ Suppression des anciennes tables...")
    conn = get_db_connection()
    cur = conn.cursor()
    
    # On supprime dans l'ordre inverse des dépendances (clés étrangères)
    tables = ["trades_history", "price_data", "macro_events", "broker_accounts", "users", "assets"]
    
    for table in tables:
        cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
    
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Base de données nettoyée.")
    
    # On relance l'initialisation avec le nouveau schéma
    init_database()

if __name__ == "__main__":
    full_reset()