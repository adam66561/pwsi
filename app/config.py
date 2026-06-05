import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-dev-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///pwsi.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    HISTORY_RETENTION_DAYS = int(os.getenv("HISTORY_RETENTION_DAYS", "365"))
