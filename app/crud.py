from sqlalchemy.orm import Session
from . import models, schemas
from .auth import get_password_hash
from typing import Optional, List

def get_user_by_phone(db: Session, phone: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.phone == phone).first()

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    print(f"Creating user with phone: {user.phone}")
    hashed_password = get_password_hash(user.password)
    print(f"Original password: {user.password}")
    print(f"Hashed password: {hashed_password}")
    
    db_user = models.User(
        name=user.name, 
        phone=user.phone, 
        password_hash=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    print(f"User created with ID: {db_user.id}")
    return db_user

def get_user_transactions(db: Session, user_id: int) -> List[models.Transaction]:
    return db.query(models.Transaction).filter(models.Transaction.user_id == user_id).all()

def create_category(db: Session, category: schemas.CategoryCreate) -> models.Category:
    db_category = models.Category(name=category.name)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def get_category_by_name(db: Session, name: str) -> Optional[models.Category]:
    return db.query(models.Category).filter(models.Category.name == name).first()

def create_transaction(db: Session, transaction: schemas.TransactionCreate, user_id: int, category_id: Optional[int]) -> models.Transaction:
    db_transaction = models.Transaction(
        type=transaction.type,
        amount=transaction.amount,
        description=transaction.description,
        user_id=user_id,
        category_id=category_id
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction 