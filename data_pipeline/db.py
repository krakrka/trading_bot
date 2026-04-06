# data_pipeline/db.py

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
NEON_DB_URL = os.getenv("NEON_DATABASE_URL")

def get_db_connection():
    """Fonction utilitaire pour obtenir une connexion partout dans le projet."""
    if not NEON_DB_URL:
        raise ValueError("ERREUR : NEON_DATABASE_URL absente.")
    return psycopg2.connect(NEON_DB_URL)

def init_database():
    """Crée l'architecture complète de la base de données FinTech SaaS."""
    
    commands = (
        # --- 1. UTILISATEURS & CONFIGURATION ---
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            full_name VARCHAR(100),
            risk_per_trade NUMERIC DEFAULT 1.0, -- Pourcentage de risque par trade (ex: 1%)
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """,
        # --- 2. COMPTES BROKERS (MT5, Binance, etc.) ---
        """
        CREATE TABLE IF NOT EXISTS broker_accounts (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            broker_name VARCHAR(50) NOT NULL,
            account_login VARCHAR(100) NOT NULL,
            encrypted_api_key TEXT NOT NULL, -- Clé chiffrée
            encrypted_secret TEXT NOT NULL,  -- Secret chiffré
            account_type VARCHAR(20) DEFAULT 'DEMO', -- DEMO ou LIVE
            status VARCHAR(20) DEFAULT 'ACTIVE'
        )
        """,
        # --- 3. ACTIFS ---
        """
        CREATE TABLE IF NOT EXISTS assets (
            asset_id SERIAL PRIMARY KEY,
            ticker VARCHAR(20) UNIQUE NOT NULL,
            asset_class VARCHAR(50) NOT NULL
        )
        """,
        # --- 4. DONNÉES DE PRIX (OHLC) ---
        """
        CREATE TABLE IF NOT EXISTS price_data (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            asset_id INTEGER REFERENCES assets(asset_id),
            open NUMERIC NOT NULL,
            high NUMERIC NOT NULL,
            low NUMERIC NOT NULL,
            close NUMERIC NOT NULL,
            volume BIGINT NOT NULL, 
            UNIQUE(timestamp, asset_id)
        )
        """,
        # --- 5. ÉVÉNEMENTS MACRO (Agent Gemini) ---
        """
        CREATE TABLE IF NOT EXISTS macro_events (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            currency VARCHAR(10) NOT NULL,
            event_name VARCHAR(255) NOT NULL,
            impact VARCHAR(50) NOT NULL,
            actual VARCHAR(50),
            forecast VARCHAR(50),
            ai_bias_score NUMERIC -- On stocke le score généré par Gemini ici aussi
        )
        """,
        # --- 6. HISTORIQUE DES TRADES (Le Track Record) ---
        """
        CREATE TABLE IF NOT EXISTS trades_history (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL, -- Null si c'est un trade global de l'IA
            timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            ticker VARCHAR(20) NOT NULL,
            direction VARCHAR(10) NOT NULL,
            entry_price NUMERIC NOT NULL,
            stop_loss NUMERIC NOT NULL,
            take_profit NUMERIC NOT NULL,
            confidence NUMERIC NOT NULL,
            pnl NUMERIC DEFAULT 0,              -- Profit ou Perte en dollars
            pnl_percentage NUMERIC DEFAULT 0,   -- Profit ou Perte en %
            status VARCHAR(20) DEFAULT 'OPEN'    -- OPEN, CLOSED, CANCELLED
        )
        """
    )
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        for command in commands:
            cur.execute(command)
            
        # Insertion/Mise à jour des actifs (Cryptos L1 incluses)
        insert_assets = """
        INSERT INTO assets (ticker, asset_class) 
        VALUES 
            ('USTEC', 'Index'), 
            ('US500', 'Index'), 
            ('XAUUSD', 'Metal'), 
            ('BTCUSD', 'Crypto'),
            ('ETHUSD', 'Crypto'),
            ('SOLUSD', 'Crypto'),
            ('ADAUSD', 'Crypto'),
            ('LINKUSD', 'Crypto'),
            ('AVAXUSD', 'Crypto'),
            ('DXY', 'Index')
        ON CONFLICT (ticker) DO NOTHING;
        """
        cur.execute(insert_assets)
        
        conn.commit()
        cur.close()
        print("✅ ARCHITECTURE SAAS INITIALISÉE : Prête pour les utilisateurs et le trading haute précision.")
        
    except Exception as e:
        print(f"❌ Erreur SQL : {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    init_database()