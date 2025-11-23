import os
import random
import requests
import uvicorn
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from dotenv import load_dotenv
import google.generativeai as genai
from sqlalchemy.orm import Session

# --- NOUVEAUX IMPORTS POUR REACT ---
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# --- Imports de nos fichiers locaux ---
from database import engine, SessionLocal
import models
import schemas
import security

# Charger les variables depuis .env (pour le développement local)
load_dotenv()

# --- Création des tables dans la DB ---
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AzTravel API",
    description="Backend API pour l'application de voyage AzTravel (Azure Ready)",
    version="1.0.0"
)

# -----------------------------------------------
# --- CONFIGURATION CORS (Azure Ready) ---
# -----------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # <--- L'étoile magique : autorise tout le monde    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------
# --- CONFIGURATIONS API & CLÉS ---
# -----------------------------------------------

city_to_iata = {
    "casablanca": "CMN", "rabat": "RBA", "marrakech": "RAK", "fès": "FEZ",
    "tanger": "TNG", "agadir": "AGA", "paris": "CDG", "marseille": "MRS",
    "lyon": "LYS", "bordeaux": "BOD", "nice": "NCE", "new york": "JFK",
    "los angeles": "LAX", "chicago": "ORD", "miami": "MIA", "madrid": "MAD",
    "barcelone": "BCN", "seville": "SVQ", "valencia": "VLC", "dubai": "DXB",
    "londres": "LHR", "rome": "FCO", "istanbul": "IST", "tokyo": "HND"
}

# TES CLÉS API
OPENWEATHER_API_KEY = "812f1cb7e3f8342b21a0e38db806d1fa"
UNSPLASH_API_KEY = "I7uY6A9E1AfsdJuA7kGaYVY3eAYUrHKj7C_fM_iN8Mk"
GEMINI_API_KEY = "AIzaSyCYzNgeKRUGcdEkvyoHe95WTdci92vIzNk" 
EXCHANGERATE_API_KEY = "6b14aa2301436f4b3ce394e9"
AVIATIONSTACK_API_KEY = "8097cdde55ac893dba7b47f94a9119c7"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash') 

# --- FONCTION DEPENDENCY DATABASE ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------------------------------
# --- AUTHENTIFICATION ---
# -----------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    
    return user

# -----------------------------------------------
# --- ROUTES PUBLIQUES (Données Voyage) ---
# -----------------------------------------------

# NOTE: J'ai supprimé l'ancienne route "/" ici pour laisser la place au Frontend React

# --- 1. LISTE DES PAYS (VERSION CORRIGÉE : LISTE FIXE) ---
@app.get("/api/countries")
def get_all_countries():
    print("--- Appel API: Récupération des pays (Mode Statique) ---")
    
    countries_list = [
        {"name": "Morocco", "currency": "MAD", "code": "MA"},
        {"name": "France", "currency": "EUR", "code": "FR"},
        {"name": "United States", "currency": "USD", "code": "US"},
        {"name": "Spain", "currency": "EUR", "code": "ES"},
        {"name": "Italy", "currency": "EUR", "code": "IT"},
        {"name": "United Kingdom", "currency": "GBP", "code": "GB"},
        {"name": "Germany", "currency": "EUR", "code": "DE"},
        {"name": "Japan", "currency": "JPY", "code": "JP"},
        {"name": "Canada", "currency": "CAD", "code": "CA"},
        {"name": "United Arab Emirates", "currency": "AED", "code": "AE"},
        {"name": "Saudi Arabia", "currency": "SAR", "code": "SA"},
        {"name": "Turkey", "currency": "TRY", "code": "TR"},
        {"name": "China", "currency": "CNY", "code": "CN"},
        {"name": "Brazil", "currency": "BRL", "code": "BR"},
        {"name": "Portugal", "currency": "EUR", "code": "PT"}
    ]
    
    countries_list.sort(key=lambda x: x["name"])
    return countries_list

# --- 2. LISTE DES VILLES (AVEC TIMEOUT ET FALLBACK) ---
@app.get("/api/cities/{country_name}")
def get_cities_by_country(country_name: str):
    formatted_name = country_name.replace("-", " ").title()
    if formatted_name.lower() in ["usa", "united states of america", "united states"]:
        formatted_name = "United States"
    if formatted_name.lower() in ["uk", "united kingdom"]:
        formatted_name = "United Kingdom"

    try:
        url = "https://countriesnow.space/api/v0.1/countries/cities"
        payload = {"country": formatted_name}
        
        # Ajout d'un timeout de 3 secondes pour ne pas bloquer
        response = requests.post(url, json=payload, timeout=3)
        data = response.json()
        
        if response.status_code != 200 or data.get("error"):
            # Fallback manuel immédiat
            return get_fallback_cities(formatted_name)
            
        return {"cities": data["data"]}
            
    except Exception as e:
        print(f"ERREUR VILLES ({e}), utilisation du fallback.")
        return get_fallback_cities(formatted_name)

def get_fallback_cities(country_name):
    if country_name == "Morocco": return {"cities": ["Casablanca", "Rabat", "Marrakech", "Fes", "Tangier", "Agadir", "Chefchaouen", "Essaouira"]}
    if country_name == "France": return {"cities": ["Paris", "Marseille", "Lyon", "Nice", "Bordeaux", "Toulouse", "Strasbourg"]}
    if country_name == "Spain": return {"cities": ["Madrid", "Barcelona", "Seville", "Valencia", "Granada"]}
    if country_name == "United States": return {"cities": ["New York", "Los Angeles", "Chicago", "Miami", "San Francisco", "Las Vegas"]}
    return {"cities": []}

# --- 3. MÉTÉO ---
@app.get("/api/weather/{city_name}")
def get_weather(city_name: str, date: Optional[str] = None):
    if date:
        temp = random.randint(15, 30)
        desc = "Ensoleillé (simulation)"
        return {
            "ville": city_name,
            "temperature": temp,
            "description": f"{desc} le {date}",
        }
    else:
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={OPENWEATHER_API_KEY}&units=metric&lang=fr"
            response = requests.get(url, timeout=3)
            if response.status_code != 200:
                return {"error": "Ville non trouvée"}
            data = response.json()
            return {
                "ville": data["name"], "temperature": round(data["main"]["temp"]),
                "description": data["weather"][0]["description"], "icon": data["weather"][0]["icon"],
                "humidite": data["main"]["humidity"]
            }
        except:
             return {"ville": city_name, "temperature": "--", "description": "Indisponible", "icon": "01d"}

# --- 4. PRÉVISIONS ---
@app.get("/api/weather/forecast/{city_name}")
def get_weather_forecast(city_name: str, start_date: Optional[str] = None):
    forecast_list = []
    for i in range(1, 6):
        forecast_list.append({
            "day_name": f"Jour {i}", 
            "full_date": f"J+{i}",
            "temp": random.randint(18, 32), 
        })
    return {"forecast": forecast_list}

# --- 5. PHOTOS ---
@app.get("/api/photos/{city_name}")
def get_city_photos(city_name: str):
    try:
        url = "https://api.unsplash.com/search/photos"
        params = {"query": f"{city_name} city landmark", "per_page": 4, "orientation": "landscape"}
        headers = {"Authorization": f"Client-ID {UNSPLASH_API_KEY}"}
        response = requests.get(url, params=params, headers=headers, timeout=4)
        if response.status_code != 200:
            return {"error": "Erreur photos", "details": response.json()}
        data = response.json()
        photos = []
        for item in data.get("results", []):
            photos.append({
                "id": item.get("id"),
                "url_small": item.get("urls", {}).get("small"),
                "alt": item.get("alt_description"),
                "photographer": item.get("user", {}).get("name")
            })
        return {"photos": photos}
    except:
        return {"photos": []}

# --- 6. VISA ---
@app.get("/api/visa/{country_name}")
def get_visa_status(country_name: str):
    c = country_name.lower()
    if "morocco" in c or "maroc" in c: return {"status": "Home", "details": "Bienvenue", "color": "blue.500"}
    if "france" in c or "spain" in c: return {"status": "Visa-Free", "details": "90 Jours", "color": "green.500"}
    if "united states" in c or "usa" in c: return {"status": "Required", "details": "Visa B1/B2", "color": "red.500"}
    return {"status": "Info Manquante", "details": "Vérifiez ambassade", "color": "yellow.500"}

# --- 7. TAUX DE CHANGE ---
@app.get("/api/currency/rate/{base}/{target}")
def get_currency_rate(base: str, target: str):
    if base.upper() == target.upper():
        return {"base": base, "target": target, "rate": 1.0}
    
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGERATE_API_KEY}/pair/{base}/{target}"
    try:
        response = requests.get(url, timeout=4)
        data = response.json()
        if response.status_code == 200 and data.get("result") == "success":
            return {"base": base, "target": target, "rate": data.get("conversion_rate")}
        return {"error": "Erreur taux"}
    except Exception:
        return {"error": "Erreur serveur"}

# --- 8. VOLS (AviationStack) ---
@app.get("/api/flights/{destination}")
def get_flights(destination: str, departure_date: Optional[str] = None):
    iata = city_to_iata.get(destination.lower())
    if not iata:
        return {"error": f"Code aéroport inconnu pour {destination}"}
    
    params = {
        'access_key': AVIATIONSTACK_API_KEY,
        'dep_iata': 'CMN', 
        'arr_iata': iata,
        'flight_date': departure_date,
        'limit': 1
    }
    
    try:
        res = requests.get("http://api.aviationstack.com/v1/flights", params=params, timeout=5)
        data = res.json()
        
        if data.get("data"):
            flight = data["data"][0]
            flight_info = {
                "price": "N/A", 
                "duration": "Direct" if flight["flight"].get("codeshared") is None else "Escale",
                "stops": 0,
                "departure_date": flight["flight_date"],
                "airline_name": flight["airline"]["name"],
                "link": f"https://www.google.com/flights?q=Vols+de+CMN+a+{iata}"
            }
            return flight_info
        return {"error": "Aucun vol trouvé ce jour-là."}
    except Exception as e:
        print(f"Erreur vol: {e}")
        return {"error": "Erreur service vol"}


# -----------------------------------------------
# --- ROUTES AUTHENTIFICATION ---
# -----------------------------------------------

@app.post("/api/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user: raise HTTPException(status_code=400, detail="Email existant")
    
    hashed_pw = security.get_password_hash(user.password)
    new_user = models.User(email=user.email, hashed_password=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/api/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    
    token = security.create_access_token(data={"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

# --- CHATBOT GEMINI ---
@app.post("/api/chat")
def chat_gemini(request: schemas.ChatRequest, current_user: schemas.User = Depends(get_current_user)):
    prompt = f"""
    Tu es "AZTravel Assistant". L'utilisateur va à {request.city}.
    Il demande : "{request.prompt}".
    Réponds de façon courte et utile.
    """
    try:
        resp = model.generate_content(prompt)
        return {"response": resp.text}
    except Exception as e:
        print(f"Erreur Gemini: {e}")
        raise HTTPException(status_code=500, detail="Erreur IA")

# --- TASKS API (CRUD) ---
@app.get("/api/tasks", response_model=List[schemas.Task])
def read_tasks(db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    return db.query(models.Task).filter(models.Task.owner_id == current_user.id).all()

@app.post("/api/tasks", response_model=schemas.Task)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    db_task = models.Task(name=task.name, owner_id=current_user.id)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@app.put("/api/tasks/{task_id}", response_model=schemas.Task)
def update_task(task_id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    db_task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.owner_id == current_user.id).first()
    if not db_task: raise HTTPException(status_code=404, detail="Tâche introuvable")
    db_task.is_done = not db_task.is_done
    db.commit()
    db.refresh(db_task)
    return db_task

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    db_task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.owner_id == current_user.id).first()
    if not db_task: raise HTTPException(status_code=404, detail="Tâche introuvable")
    db.delete(db_task)
    db.commit()
    return {"ok": True}

@app.get("/api/tasks/stats")
def get_stats(db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    query = db.query(models.Task).filter(models.Task.owner_id == current_user.id)
    return {"total_tasks": query.count(), "pending_tasks": query.filter(models.Task.is_done == False).count()}

# --- PROFIL UTILISATEUR ---
@app.get("/api/users/me", response_model=schemas.User)
def read_users_me(current_user: schemas.User = Depends(get_current_user)):
    return current_user

@app.put("/api/users/me/password")
def change_password(passwords: schemas.UserChangePassword, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not security.verify_password(passwords.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Ancien mot de passe incorrect")
    current_user.hashed_password = security.get_password_hash(passwords.new_password)
    db.commit()
    return {"message": "Mot de passe mis à jour"}


# =================================================================
# --- INTEGRATION DU FRONTEND REACT (STATIC FILES) ---
# =================================================================

# On vérifie si le dossier "static" existe
if os.path.exists("static"):

    # 1. Montage des fichiers CSS/JS de React
    app.mount("/static", StaticFiles(directory="static/static"), name="static")

    # 2. Route racine qui affiche le site React
    @app.get("/")
    async def read_root():
        return FileResponse('static/index.html')

    # 3. Gestion des erreurs 404 (Pour le routing React)
    @app.exception_handler(404)
    async def custom_404_handler(request, exc):
        # Si c'est une API, on renvoie une erreur JSON
        if request.url.path.startswith("/api"):
            return {"error": "API Endpoint not found"}, 404
        
        # Sinon, on renvoie le site React
        return FileResponse('static/index.html')

else:
    print("⚠️ AVERTISSEMENT : Dossier 'static' introuvable. Le site React ne s'affichera pas.")


if __name__ == "__main__":
    # En production Azure, Gunicorn est utilisé à la place.
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)