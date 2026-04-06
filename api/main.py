# api/main.py

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr
from typing import List
import os

# Import des modules locaux
from core.auth import hash_password, verify_password, create_access_token
from data_pipeline.db import get_db_connection

# Initialisation de FastAPI et des templates
app = FastAPI(title="Nexa AI Trading SaaS", version="1.2.0")
templates = Jinja2Templates(directory="templates")

# --- MODÈLES DE DONNÉES (Pydantic) ---

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class Token(BaseModel):
    access_token: str
    token_type: str

# --- ROUTES DE NAVIGATION (FRONTEND) ---

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Page d'accueil simple ou redirection."""
    return templates.TemplateResponse(
        request=request, 
        name="login.html"
    )

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Affiche la page de connexion."""
    return templates.TemplateResponse(
        request=request, 
        name="login.html"
    )

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Affiche le dashboard principal."""
    return templates.TemplateResponse(
        request=request, 
        name="index.html"
    )

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Affiche la page d'inscription."""
    return templates.TemplateResponse(
        request=request, 
        name="register.html"
    )
# --- ROUTES D'AUTHENTIFICATION (API) ---

@app.post("/auth/register", status_code=201)
def register(user: UserCreate):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Vérifier si l'utilisateur existe déjà
    cur.execute("SELECT id FROM users WHERE email = %s", (user.email,))
    if cur.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Cet email est déjà enregistré.")
    
    # Hachage et insertion
    hashed = hash_password(user.password)
    try:
        cur.execute(
            "INSERT INTO users (email, hashed_password, full_name) VALUES (%s, %s, %s)",
            (user.email, hashed, user.full_name)
        )
        conn.commit()
        return {"message": "Compte créé avec succès."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur base de données : {e}")
    finally:
        conn.close()

@app.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT id, hashed_password FROM users WHERE email = %s", (form_data.username,))
    user = cur.fetchone()
    conn.close()
    
    if not user or not verify_password(form_data.password, user[1]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Génération du JWT
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

# --- ROUTES DE DONNÉES (API) ---

@app.get("/trades/history")
def get_trades_history():
    """Récupère les signaux générés par le bot_daemon."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT ticker, direction, entry_price, confidence, timestamp 
            FROM trades_history 
            ORDER BY timestamp DESC LIMIT 20
        """)
        trades = cur.fetchall()
        return [
            {
                "ticker": t[0], 
                "direction": t[1], 
                "price": float(t[2]), 
                "confidence": float(t[3]), 
                "time": t[4]
            } for t in trades
        ]
    finally:
        conn.close()

@app.get("/account/info")
def get_account_info():
    """Données simulées du compte broker (à lier à une API Broker plus tard)."""
    # Ici, nous simulons une réponse que ton frontend index.html pourra lire
    return {
        "status": "Connecté",
        "broker": "MetaTrader 5",
        "balance": 10452.30,
        "equity": 10497.15,
        "daily_pnl": 142.85,
        "active_positions": [
            {
                "ticker": "BTCUSD", 
                "direction": "ACHAT", 
                "pnl": 45.20, 
                "entry": 69455.77
            },
            {
                "ticker": "SOLUSD", 
                "direction": "VENTE", 
                "pnl": -12.40, 
                "entry": 82.51
            }
        ]
    }

# --- DÉMARRAGE ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)