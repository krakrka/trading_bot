from fastapi import APIRouter

# Création du routeur spécifique au trading
router = APIRouter(
    prefix="/trading",
    tags=["Trading Engine"]
)

@router.get("/signals")
async def get_live_signals():
    """
    (Bêta) Renvoie les derniers signaux générés par l'IA en direct.
    Plus tard, cette route interrogera la base de données Neon ou le cache Redis.
    """
    return {
        "status": "success",
        "data": {
            "BTCUSD": {"direction": "VENTE", "confidence": 61.04, "entry": 67474.11, "sl": 67690.99, "tp": 67040.35},
            "USTEC": {"direction": "NEUTRAL", "confidence": 52.16, "message": "En attente d'avantage statistique"}
        }
    }

@router.get("/history")
async def get_track_record():
    """Renvoie l'historique des trades pour afficher le graphique de rentabilité sur le web."""
    return {"status": "success", "message": "Historique en cours de construction..."}