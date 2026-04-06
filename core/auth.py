# core/auth.py

import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

# Configuration Secrète (À mettre dans ton .env)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "UNE_CLE_TRES_SECRETE_POUR_TON_PROJET_NEXA_2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # Le token dure 24h

# Gestionnaire de hachage (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Transforme un mot de passe en texte clair en empreinte sécurisée."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie si le mot de passe saisi correspond à l'empreinte en base."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Génère un Token JWT pour authentifier l'utilisateur sur l'API."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    """Vérifie et décode un token reçu par l'API."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload if payload.get("exp") >= datetime.utcnow().timestamp() else None
    except JWTError:
        return None