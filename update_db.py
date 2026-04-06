import psycopg2

DB_URL = "postgresql://neondb_owner:npg_HqDy0RlNZhC4@ep-steep-surf-a9fg3uwf-pooler.gwc.azure.neon.tech/neondb?sslmode=require&channel_binding=require"

def force_reset_table():
    print("⏳ Connexion à Neon...")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # 1. On détruit brutalement l'ancienne table si elle existe
        print("🗑️ Suppression de l'ancienne table...")
        cur.execute("DROP TABLE IF EXISTS broker_accounts CASCADE;")
        
        # 2. On recrée la table avec la structure parfaite
        print("🏗️ Création de la nouvelle table...")
        cur.execute("""
        CREATE TABLE broker_accounts (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            broker_name VARCHAR(50),
            api_key TEXT,
            api_secret TEXT,
            account_type VARCHAR(20) DEFAULT 'MANUAL',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        print("✅ INCROYABLE ! La table est toute neuve et prête !")
    except Exception as e:
        print(f"❌ ERREUR : {e}")

if __name__ == "__main__":
    force_reset_table()