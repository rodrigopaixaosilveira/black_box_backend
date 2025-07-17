from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from . import crud, schemas
import hashlib

# Configurações de segurança
SECRET_KEY = "your-secret-key-here"  # Em produção, use variável de ambiente
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Função auxiliar para evitar importação circular
def get_db():
    from .database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    # Hash simples usando SHA-256
    hashed = hashlib.sha256(plain_password.encode()).hexdigest()
    return hashed == hashed_password

def get_password_hash(password):
    # Hash simples usando SHA-256
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(db: Session, phone: str, password: str):
    print(f"=== AUTHENTICATE USER ===")
    print(f"Phone: {phone}")
    print(f"Password: {password}")
    
    user = crud.get_user_by_phone(db, phone)
    print(f"User found: {user is not None}")
    
    if not user:
        print("User not found")
        return False
    
    print(f"User password hash: {user.password_hash}")
    password_valid = verify_password(password, user.password_hash)
    print(f"Password valid: {password_valid}")
    
    if not password_valid:
        print("Password verification failed")
        return False
    
    print("Authentication successful")
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        phone: str = payload.get("sub")
        if phone is None:
            raise credentials_exception
        token_data = schemas.TokenData(phone=phone)
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_phone(db, phone=token_data.phone)
    if user is None:
        raise credentials_exception
    return user 