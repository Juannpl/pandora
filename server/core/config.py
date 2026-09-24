import os


def required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value or not value.strip():
        raise RuntimeError(f"La variable d’environnement {name} doit être définie.")
    return value


SECRET_KEY = required_env("SECRET_KEY")
DATABASE_URL = required_env("DATABASE_URL")
