import os
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier

# S'assurer que le dossier existe
os.makedirs("core/ai_models", exist_ok=True)

ASSETS = ['USTEC', 'US500', 'XAUUSD', 'BTCUSD', 'ETHUSD', 'SOLUSD', 'ADAUSD', 'LINKUSD', 'AVAXUSD']

print("🛠️ Génération des modèles factices pour le test de l'architecture...")

for asset in ASSETS:
    # Création d'un modèle basique
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    
    # Entraînement sur des données bidons (7 features, comme dans ton bot_daemon)
    X_dummy = np.random.rand(100, 7) 
    y_dummy = np.random.randint(2, size=100) # 0 ou 1
    
    model.fit(X_dummy, y_dummy)
    
    # Sauvegarde dans le bon dossier
    joblib.dump(model, f"core/ai_models/model_{asset}.pkl")
    print(f"   ✅ Modèle factice généré : model_{asset}.pkl")