from fastapi import APIRouter

router = APIRouter(
    prefix="/users",
    tags=["SaaS Users"]
)

@router.post("/register")
async def register_user():
    """Route pour créer un nouveau compte client."""
    return {"message": "Endpoint de création de compte à coder."}

@router.get("/portfolio/{user_id}")
async def get_user_portfolio(user_id: int):
    """Récupère l'état du compte MT5/Broker connecté par l'utilisateur."""
    return {"user_id": user_id, "status": "Compte de trading non lié."}