import os
from dotenv import load_dotenv
from pathlib import Path

# Caminho para o arquivo .env na pasta backend/
# Se config.py está em backend/app/core/, então Path(__file__).resolve().parent.parent.parent leva para backend/
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

SECRET_KEY = os.getenv("SECRET_KEY", "a_super_secret_key_for_dev_only_change_it_in_production") # Carrega do .env ou usa um default
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # O token expira em 30 minutos

# Você pode adicionar outras configurações aqui, como URLs de banco de dados, etc.
# Ex:
# PROJECT_NAME = "Programa Educacional Inclusivo"
# API_V1_STR = "/api/v1" 