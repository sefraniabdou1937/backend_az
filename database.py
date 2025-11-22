from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Définition des variables d'Azure (que nous avons configurées)
SERVER = os.getenv("SQL_SERVER_NAME")
DATABASE = os.getenv("SQL_DB_NAME")
USERNAME = os.getenv("SQL_USER")
PASSWORD = os.getenv("SQL_PASSWORD")

# 1. Vérifie si les variables Azure SQL existent (si OUI, c'est la prod sur Azure)
if SERVER and DATABASE and USERNAME and PASSWORD:
    # Construire la chaîne de connexion MSSQL (nécessite pyodbc)
    SQLALCHEMY_DATABASE_URL = (
        f"mssql+pyodbc://{USERNAME}:{PASSWORD}@{SERVER}:1433/{DATABASE}"
        f"?driver=ODBC+Driver+17+for+SQL+Server"
    )
    # L'engine est créé ici sans le check_same_thread
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

else:
    # 2. Logique pour le développement local (SQLite, ou votre binôme peut y mettre Postgres local)
    SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./travel.db")
    
    # Si on utilise SQLite (local), on a besoin du check_same_thread
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
        )
    else:
        # Si c'est un autre type de DB locale (Postgres local par ex)
        engine = create_engine(SQLALCHEMY_DATABASE_URL)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()