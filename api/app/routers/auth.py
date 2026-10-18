from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
import bcrypt
from datetime import timedelta
from ..auth import FAKE_USERS_DB, create_access_token

router = APIRouter()

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Route de connexion qui génère le Token JWT"""
    user = FAKE_USERS_DB.get(form_data.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    try:
        # Vérification directe avec bcrypt
        password_bytes = form_data.password.encode('utf-8')
        hashed_bytes = user["hashed_password"].encode('utf-8')
        
        if not bcrypt.checkpw(password_bytes, hashed_bytes):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Nom d'utilisateur ou mot de passe incorrect",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Erreur d'authentification",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # On crée le badge (token) valable 30 minutes
    access_token = create_access_token(
        data={"sub": user["username"]}, 
        expires_delta=timedelta(minutes=30)
    )
    return {"access_token": access_token, "token_type": "bearer"}