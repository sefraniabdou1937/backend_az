from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext

# --- Configuration du Hachage de Mot de Passe ---
# On dit à passlib d'utiliser l'algorithme "bcrypt"
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")# C'est ce qui garantit que tes tokens ne peuvent pas être falsifiés.
SECRET_KEY = "aztravel-project-by-abdou-and-zayd-2025!" # Change ça pour une phrase aléatoire
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Le laissez-passer expirera après 30 minutes

# --- FONCTIONS ---

def verify_password(plain_password, hashed_password):
    """Vérifie si un mot de passe en clair correspond à un mot de passe haché."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Renvoie le hachage d'un mot de passe."""
    return pwd_context.hash(password)

# 

def create_access_token(data: dict):
    """Crée un nouveau token (laissez-passer) JWT."""
    to_encode = data.copy()
    
    # Ajoute une date d'expiration au token
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    # Chiffre le token avec la clé secrète
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt