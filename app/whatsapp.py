import re
from sqlalchemy.orm import Session
from . import crud, schemas

def parse_whatsapp_message(message: str):
    # Exemplo: "gasto 50 almoco #lanche"
    pattern = r"^(gasto|ganho) (\d+[\.,]?\d*) ([^#]+)(?: #(\w+))?"
    match = re.match(pattern, message.strip(), re.IGNORECASE)
    if not match:
        return None
    tipo = match.group(1).lower()
    valor = float(match.group(2).replace(",", "."))
    descricao = match.group(3).strip()
    categoria = match.group(4) if match.group(4) else None
    return {
        "type": tipo,
        "amount": valor,
        "description": descricao,
        "category": categoria
    }

def process_whatsapp_message(db: Session, phone: str, message: str):
    data = parse_whatsapp_message(message)
    if not data:
        return {"error": "Mensagem inválida"}
    user = crud.get_user_by_phone(db, phone)
    if not user:
        user = crud.create_user(db, schemas.UserCreate(name=phone, phone=phone))
    category_id = None
    if data["category"]:
        category = crud.get_category_by_name(db, data["category"])
        if not category:
            category = crud.create_category(db, schemas.CategoryCreate(name=data["category"]))
        category_id = category.id
    transaction_in = schemas.TransactionCreate(
        type=data["type"],
        amount=data["amount"],
        description=data["description"],
        category_id=category_id
    )
    transaction = crud.create_transaction(db, transaction_in, user.id, category_id)
    return {"success": True, "transaction_id": transaction.id} 