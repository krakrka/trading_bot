# data_pipeline/fetchers.py

import yfinance as yf
import pandas as pd
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from data_pipeline.db import get_db_connection

# Ajout des cryptos "fondamentales" (Layer 1 et utilitaires majeurs), exclusion des meme coins
ASSETS_MAPPING = {
    'USTEC': 'NQ=F',      # NASDAQ 100
    'US500': 'ES=F',      # S&P 500
    'XAUUSD': 'GC=F',     # Or
    'BTCUSD': 'BTC-USD',  # Bitcoin
    'ETHUSD': 'ETH-USD',  # Ethereum
    'SOLUSD': 'SOL-USD',  # Solana
    'ADAUSD': 'ADA-USD',  # Cardano
    'LINKUSD': 'LINK-USD',# Chainlink
    'AVAXUSD': 'AVAX-USD',# Avalanche
    'DXY': 'UUP'          # Dollar Index
}

def update_price_data():
    """Télécharge l'historique de prix depuis Yahoo Finance et le met en base."""
    print("📈 Mise à jour des données de prix...")
    conn = get_db_connection()
    cur = conn.cursor()

    for db_ticker, yf_ticker in ASSETS_MAPPING.items():
        try:
            cur.execute("SELECT asset_id FROM assets WHERE ticker = %s", (db_ticker,))
            result = cur.fetchone()
            if not result:
                continue
            asset_id = result[0]

            data = yf.download(yf_ticker, period="700d", interval="1h", progress=False)
            if data.empty: 
                continue

            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            data = data.reset_index()
            date_col = 'Datetime' if 'Datetime' in data.columns else 'Date'
            
            inserted = 0
            for index, row in data.iterrows():
                try:
                    cur.execute("""
                        INSERT INTO price_data (timestamp, asset_id, open, high, low, close, volume)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (timestamp, asset_id) DO NOTHING
                    """, (row[date_col], asset_id, float(row['Open']), float(row['High']), float(row['Low']), float(row['Close']), int(row['Volume'])))
                    if cur.rowcount > 0: 
                        inserted += 1
                except Exception: 
                    continue
            
            conn.commit()
            print(f"   ✅ {inserted} nouvelles bougies pour {db_ticker}.")
        except Exception as e:
            print(f"   ❌ Erreur sur {db_ticker} : {e}")

    cur.close()
    conn.close()

def update_macro_calendar():
    """Télécharge le calendrier économique et le met en base."""
    print("🌍 Mise à jour du calendrier macroéconomique...")
    url = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return
            
        root = ET.fromstring(response.content)
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Nettoyage des événements futurs pour éviter les doublons lors des mises à jour
        cur.execute("DELETE FROM macro_events WHERE timestamp >= CURRENT_DATE")
        
        inserted = 0
        for item in root.findall('event'):
            date_str = item.find('date').text
            time_str = item.find('time').text
            
            if time_str in ["All Day", "Tentative"]:
                continue
                
            try:
                dt_str = f"{date_str} {time_str}"
                timestamp = datetime.strptime(dt_str, "%m-%d-%Y %I:%M%p")
            except Exception:
                continue
                
            currency = item.find('country').text
            impact = item.find('impact').text
            
            # Filtre : Uniquement les news USD High/Medium impact
            if currency == 'USD' and impact in ['High', 'Medium']:
                title = item.find('title').text
                forecast = item.find('forecast').text if item.find('forecast') is not None else ''
                
                cur.execute("""
                    INSERT INTO macro_events (timestamp, currency, event_name, impact, actual, forecast)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (timestamp, currency, title, impact, '', forecast))
                inserted += 1
                
        conn.commit()
        cur.close()
        conn.close()
        print(f"   ✅ {inserted} événements macro enregistrés.")
        
    except Exception as e:
        print(f"   ❌ Erreur Macro : {e}")

if __name__ == "__main__":
    # Exécution des deux pipelines de données
    update_macro_calendar()
    update_price_data()