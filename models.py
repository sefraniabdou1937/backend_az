from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base  # On importe la Base de notre fichier database.py

#
# NOUVEAU: Modèle pour les utilisateurs
#
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String) # On stocke le mdp haché
    
    # Ceci crée le lien "magique"
    # Python pourra voir user.tasks (toutes les tâches de cet user)
    tasks = relationship("Task", back_populates="owner")

#
# MODIFIÉ: Modèle pour les tâches
#
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    is_done = Column(Boolean, default=False)
    
    # --- NOUVEAU LIEN ---
    # C'est la "clé étrangère" (Foreign Key)
    # On dit à la table Task qu'elle doit avoir un ID de propriétaire
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # Lien retour vers le propriétaire
    owner = relationship("User", back_populates="tasks")