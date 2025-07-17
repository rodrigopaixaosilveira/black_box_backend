from fastapi import FastAPI, Depends, Request, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta
from .database import SessionLocal, init_db
from . import whatsapp, crud, schemas, auth
from .auth import ACCESS_TOKEN_EXPIRE_MINUTES, get_db

app = FastAPI()

# Adicionar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

@app.post("/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    print(f"Register attempt - name: {user.name}, phone: {user.phone}")
    db_user = crud.get_user_by_phone(db, phone=user.phone)
    if db_user:
        print("Phone already registered")
        raise HTTPException(status_code=400, detail="Phone already registered")
    new_user = crud.create_user(db=db, user=user)
    print(f"User created successfully - id: {new_user.id}")
    return new_user

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    print(f"=== LOGIN ATTEMPT ===")
    print(f"Form data received: {form_data}")
    print(f"Username: {form_data.username}")
    print(f"Password: {form_data.password}")
    print(f"Form data type: {type(form_data)}")
    
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        print("Authentication failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect phone or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.phone}, expires_delta=access_token_expires
    )
    print("Login successful")
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: schemas.User = Depends(auth.get_current_user)):
    return current_user

@app.get("/transactions", response_model=list[schemas.Transaction])
async def get_transactions(current_user: schemas.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    transactions = crud.get_user_transactions(db, current_user.id)
    return transactions

@app.post("/transactions", response_model=schemas.Transaction)
async def create_transaction(
    transaction: schemas.TransactionCreate, 
    current_user: schemas.User = Depends(auth.get_current_user), 
    db: Session = Depends(get_db)
):
    category_id = None
    if transaction.category_id:
        category = db.query(schemas.Category).filter(schemas.Category.id == transaction.category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        category_id = category.id
    
    return crud.create_transaction(db, transaction, current_user.id, category_id)

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    # Espera-se um JSON com {"phone": "...", "message": "..."}
    data = await request.json()
    phone = data.get("phone")
    message = data.get("message")
    result = whatsapp.process_whatsapp_message(db, phone, message)
    return result

@app.get("/")
def read_root():
    return {"message": "Backend de Gestão Financeira rodando!"} 