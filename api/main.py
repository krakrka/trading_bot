# api/main.py

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr
import os

# Import des modules locaux
from core.auth import hash_password, verify_password, create_access_token, decode_access_token
from data_pipeline.db import get_db_connection

# Initialisation
app = FastAPI(title="Nexa AI Trading SaaS", version="2.0.0")
templates = Jinja2Templates(directory="templates")

# Système de sécurité pour lire le Token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# --- MODÈLES DE DONNÉES (Pydantic) ---

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class Token(BaseModel):
    access_token: str
    token_type: str

class BrokerAccountSchema(BaseModel):
    broker: str
    key: str
    secret: str

# --- FONCTION DE SÉCURITÉ ---

def get_current_user(token: str = Depends(oauth2_scheme)):
    """Décode le Token JWT et identifie l'utilisateur."""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide ou expiré")
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, email, full_name FROM users WHERE email = %s", (payload.get("sub"),))
    user = cur.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur non trouvé")
    
    return {"id": user[0], "email": user[1], "full_name": user[2]}

# --- ROUTES DE NAVIGATION (FRONTEND) ---

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(request=request, name="register.html")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

# --- ROUTES D'AUTHENTIFICATION (API) ---

@app.post("/auth/register", status_code=201)
def register(user: UserCreate):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT id FROM users WHERE email = %s", (user.email,))
    if cur.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Cet email est déjà enregistré.")
    
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
    
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

# --- ROUTES DE TRADING & COMPTES (API) ---

@app.post("/api/accounts/add")
def add_account(data: BrokerAccountSchema, current_user: dict = Depends(get_current_user)):
    """Ajoute une clé d'API Broker de manière sécurisée pour l'utilisateur connecté."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO broker_accounts (user_id, broker_name, api_key, api_secret) VALUES (%s, %s, %s, %s)",
            (current_user["id"], data.broker, data.key, data.secret)
        )
        conn.commit()
        return {"status": "success", "message": "Clés enregistrées avec succès"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'enregistrement : {e}")
    finally:
        conn.close()

@app.get("/trades/history")
def get_trades_history():
    """Récupère les signaux générés par l'IA."""
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
            {"ticker": t[0], "direction": t[1], "price": float(t[2]), "confidence": float(t[3]), "time": t[4]} 
            for t in trades
        ]
    finally:
        conn.close()

@app.get("/account/info")
def get_account_info():
    """Simule la récupération du PnL et des positions ouvertes."""
    return {
        "status": "Connecté",
        "balance": 10452.30,
        "equity": 10497.15,
        "daily_pnl": 142.85,
        "active_positions": [
            {"ticker": "BTCUSD", "direction": "ACHAT", "pnl": 45.20, "entry": 69455.77},
            {"ticker": "SOLUSD", "direction": "VENTE", "pnl": -12.40, "entry": 82.51}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)