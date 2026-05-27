import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 280,  # Recicla las conexiones cada 4 minutos y medio
        "pool_pre_ping": True # Verifica si la conexión sigue viva antes de usarlaSQLALCHEMY_ENGINE_OPTIONS = {
    }