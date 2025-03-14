import os
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные окружения из файла .env

class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///site.db")  # URL базы данных

