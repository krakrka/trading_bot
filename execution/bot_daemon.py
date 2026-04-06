# execution/bot_daemon.py

import os
import time
import joblib
import yfinance as yf
import pandas as pd
import warnings
from datetime import datetime, timedelta
from dotenv import load_dotenv

from data_pipeline.db import get_db_connection
from core.trade_manager import calculate_position
from core.nlp_agent.macro_analyzer import analyze_macro_event

warnings.filterwarnings('ignore')
load_dotenv()

ASSETS = {
    'USTEC': 'NQ=F', 'US500': 'ES=F', 'XAUUSD': 'GC=F', 
    'BTCUSD': 'BTC-USD', 'ETHUSD': 'ETH-USD', 'SOLUSD': 'SOL-USD', 
    'ADAUSD': 'ADA-USD', 'LINKUSD': 'LINK-USD', 'AVAXUSD': 'AVAX-USD'
}
DXY_TICKER = 'UUP'
MACRO_WEIGHT = 5.0 # Chaque point de biais Macro ajoute ou retire 5% de probabilité

def log_trade_to_db(ticker, plan, confidence):
    """Enregistre le trade avec le nouveau schéma SaaS."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO trades_history (ticker, direction, entry_price, stop_loss, take_profit, confidence)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            ticker, 
            plan["direction"], 
            plan["entry_price"], 
            plan["stop_loss"], 
            plan["take_profit"], 
            confidence
        ))
        conn.commit()
        cur.close()
        conn.close()
        print(f"   📁 Trade {plan['direction']} sur {ticker} enregistré en base de données.")
    except Exception as e:
        print(f"   ❌ Erreur SQL (Historique) : {e}")

def calculate_live_features(df_asset, df_dxy):
    """Calcule les indicateurs techniques (RSI, ATR, Volatilité) pour l'IA."""
    df_asset.index = df_asset.index.tz_localize(None)
    df_dxy.index = df_dxy.index.tz_localize(None)
    
    df_asset['hour'] = df_asset.index.hour
    df_asset['day_of_week'] = df_asset.index.dayofweek
    df_asset['return_1h'] = df_asset['Close'].pct_change(1)
    df_asset['return_5h'] = df_asset['Close'].pct_change(5)
    df_asset['ATR'] = (df_asset['High'] - df_asset['Low']).rolling(window=14).mean()
    df_dxy['dxy_return_1h'] = df_dxy['Close'].pct_change(1)
    
    df = pd.merge(df_asset, df_dxy[['dxy_return_1h']], left_index=True, right_index=True, how='left')
    df['dxy_return_1h'] = df['dxy_return_1h'].ffill().fillna(0)
    df['volatility_10'] = df['return_1h'].rolling(window=10).std()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI_14'] = 100 - (100 / (1 + (gain / loss)))
    
    return df.dropna()

def get_latest_macro_bias():
    """Récupère la dernière news impactante et demande l'analyse de Gemini en direct."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        now = datetime.now()
        past_window = now - timedelta(hours=24) # On regarde les news des dernières 24h
        
        cur.execute("""
            SELECT event_name, actual, forecast FROM macro_events 
            WHERE currency = 'USD' AND impact = 'High' AND actual != ''
            AND timestamp BETWEEN %s AND %s
            ORDER BY timestamp DESC LIMIT 1
        """, (past_window, now))
        
        news = cur.fetchone()
        cur.close()
        conn.close()
        
        if news:
            print(f"📰 News Macro détectée : {news[0]} (Actuel: {news[1]}, Prévu: {news[2]})")
            bias_json = analyze_macro_event(news[0], news[1], news[2])
            return bias_json
        return None
    except Exception:
        return None

def scan_markets():
    print(f"\n{'='*60}")
    print(f"📡 DAEMON TRADING HYBRIDE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    # Étape 1 : Récupération de l'intelligence fondamentale
    macro_context = get_latest_macro_bias()
    if macro_context:
        print(f"🧠 Score Macro Actif -> NASDAQ: {macro_context.get('nasdaq_bias')}, CRYPTO: {macro_context.get('crypto_bias')}")
        print(f"   Raisonnement : {macro_context.get('reasoning')}\n")
    else:
        print("🌍 Aucun événement macro majeur récent. Focus 100% Quantitatif.\n")

    try:
        dxy_data = yf.download(DXY_TICKER, period="5d", interval="1h", progress=False)
        if isinstance(dxy_data.columns, pd.MultiIndex): dxy_data.columns = dxy_data.columns.get_level_values(0)
    except Exception: 
        print("❌ Erreur DXY")
        return

    features_list = ['return_1h', 'return_5h', 'dxy_return_1h', 'volatility_10', 'RSI_14', 'hour', 'day_of_week']

    for name, ticker in ASSETS.items():
        model_path = f"core/ai_models/model_{name}.pkl"
        if not os.path.exists(model_path): 
            print(f"[{name}] ⚠️ Modèle IA introuvable.")
            continue
            
        model = joblib.load(model_path)
        asset_data = yf.download(ticker, period="5d", interval="1h", progress=False)
        
        if isinstance(asset_data.columns, pd.MultiIndex): asset_data.columns = asset_data.columns.get_level_values(0)
        if asset_data.empty: continue
            
        live_df = calculate_live_features(asset_data, dxy_data)
        if live_df.empty: continue
            
        current_state = live_df[features_list].iloc[-1:]
        
        # 1. Probabilité purement Quantitative
        ml_prediction = model.predict(current_state)[0]
        base_prob = float(max(model.predict_proba(current_state)[0]) * 100)
        direction = "ACHAT" if ml_prediction == 1 else "VENTE"
        
        # 2. Fusion avec le Biais Fondamental
        final_prob = base_prob
        if macro_context:
            if name in ['USTEC', 'US500']: active_bias = macro_context.get('nasdaq_bias', 0)
            elif name in ['BTCUSD', 'ETHUSD', 'SOLUSD', 'ADAUSD', 'LINKUSD', 'AVAXUSD']: active_bias = macro_context.get('crypto_bias', 0)
            else: active_bias = 0
                
            if direction == "ACHAT": final_prob += (active_bias * MACRO_WEIGHT)
            else: final_prob -= (active_bias * MACRO_WEIGHT)

        if final_prob < 55.0:
            print(f"[{name}] ⏳ Signal rejeté (Confiance Finale : {final_prob:.2f}%)")
            continue
            
        current_price = float(live_df['Close'].iloc[-1])
        current_atr = float(live_df['ATR'].iloc[-1])
        
        trade_plan = calculate_position(current_price, current_atr, 1 if direction == "ACHAT" else 0)
        color = "\033[92m" if direction == "ACHAT" else "\033[91m"
        
        print(f"[{name}] {color}{direction}\033[0m validé à {final_prob:.2f}% (ML: {base_prob:.1f}%)")
        # Dans execution/bot_daemon.py, remplace l'affichage final :
        print(f"   🎯 Prix : {trade_plan['entry_price']} | 🛡️ SL : {trade_plan['stop_loss']} | 💰 TP : {trade_plan['take_profit']}")
        
        log_trade_to_db(name, trade_plan, final_prob)

if __name__ == "__main__":
    scan_markets()