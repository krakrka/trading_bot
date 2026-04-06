# model_trainer.py
import pandas as pd
import joblib
import warnings
from sklearn.ensemble import RandomForestClassifier
from data_pipeline.db import get_db_connection

# On ignore les alertes SQLAlchemy de pandas pour plus de clarté
warnings.filterwarnings("ignore", category=UserWarning)

def train_all_models():
    conn = get_db_connection()
    assets = pd.read_sql("SELECT asset_id, ticker FROM assets", conn)
    
    print("🧠 DÉMARRAGE DE L'ENTRAÎNEMENT DES MODÈLES RÉELS...")

    for _, row in assets.iterrows():
        asset_id, ticker = row['asset_id'], row['ticker']
        if ticker == 'DXY': continue 

        # 1. Chargement des données de l'actif
        query_asset = f"SELECT timestamp, close, high, low FROM price_data WHERE asset_id = {asset_id} ORDER BY timestamp ASC"
        df = pd.read_sql(query_asset, conn)
        
        # 2. Chargement du DXY séparément pour éviter les erreurs de jointure
        query_dxy = "SELECT timestamp, close as dxy_close FROM price_data WHERE asset_id = (SELECT asset_id FROM assets WHERE ticker = 'DXY') ORDER BY timestamp ASC"
        df_dxy = pd.read_sql(query_dxy, conn)

        if len(df) < 200 or len(df_dxy) < 200:
            print(f"   ⚠️ Pas assez de données pour {ticker} ({len(df)} lignes).")
            continue

        # Fusion propre des données sur le timestamp
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df_dxy['timestamp'] = pd.to_datetime(df_dxy['timestamp'])
        df = pd.merge_asof(df, df_dxy, on='timestamp', direction='nearest')

        # 3. Feature Engineering
        df['return_1h'] = df['close'].pct_change(1)
        df['return_5h'] = df['close'].pct_change(5)
        df['dxy_return_1h'] = df['dxy_close'].pct_change(1)
        df['volatility_10'] = df['return_1h'].rolling(window=10).std()
        
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        df['RSI_14'] = 100 - (100 / (1 + (gain / loss + 1e-9))) # +1e-9 pour éviter division par zéro
        
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        
        # Target : Est-ce que le prix sera plus haut dans 1 bougie ?
        df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
        
        features = ['return_1h', 'return_5h', 'dxy_return_1h', 'volatility_10', 'RSI_14', 'hour', 'day_of_week']
        df_train = df.dropna()

        if len(df_train) < 100:
            print(f"   ⚠️ Données insuffisantes après calcul des indicateurs pour {ticker}.")
            continue

        # 4. Entraînement
        X = df_train[features]
        y = df_train['target']
        
        model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
        model.fit(X, y)

        # 5. Sauvegarde
        joblib.dump(model, f"core/ai_models/model_{ticker}.pkl")
        print(f"   ✅ Modèle entraîné pour {ticker} ({len(df_train)} bougies)")

    conn.close()
    print("\n🚀 TOUS LES MODÈLES SONT PRÊTS POUR LA PRODUCTION.")

if __name__ == "__main__":
    train_all_models()