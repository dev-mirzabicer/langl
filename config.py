# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # If not provided, defaults to an in-project SQLite DB named language_app.db
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///language_app.db')
    SQLALCHEMY_ECHO = False  # Set True to debug SQL queries
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DEEPL_API_KEY = os.environ.get('DEEPL_API_KEY', 'e686b367-4171-4fed-a77e-1d55a68778ab:fx')
    # For advanced usage, you might store other configuration here (e.g. SECRET_KEY).
