from pydantic import BaseModel
from typing import List, Optional

# ==================================
# Schémas pour les Tâches (Tasks)
# ==================================

class TaskCreate(BaseModel):
    name: str

class Task(BaseModel):
    id: int
    name: str
    is_done: bool
    owner_id: int

    class Config:
        orm_mode = True

# ==================================
# Schémas pour les Utilisateurs (Users)
# ==================================

class UserCreate(BaseModel):
    email: str
    password: str

class User(BaseModel):
    id: int
    email: str
    tasks: List[Task] = []

    class Config:
        orm_mode = True

# ==================================
# Schémas pour le Token (Login)
# ==================================

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# ==================================
# Schéma pour le Chatbot
# ==================================
class ChatRequest(BaseModel):
    prompt: str
    city: str

# ==================================
# NOUVEAU : Schéma pour Changer le Mot de Passe
# ==================================
class UserChangePassword(BaseModel):
    old_password: str
    new_password: str