from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import jwt
from core.config import SECRET_KEY

# Configuration de la sécurité
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Fonctions de hachage de mot de passe
def hash_password(password: str) -> str:
    """Hache le mot de passe en utilisant bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie si le mot de passe en clair correspond au mot de passe haché."""
    return pwd_context.verify(plain_password, hashed_password)

# Fonctions de création de jeton d'accès
def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Crée un jeton d'accès avec les données fournies et une date d'expiration."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
