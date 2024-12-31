# db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import Config
from models import Base

class DBService:
    def __init__(self):
        self.engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, echo=Config.SQLALCHEMY_ECHO)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_tables(self):
        """
        Creates all tables in the database. Should be called once at startup.
        """
        Base.metadata.create_all(self.engine)

    def get_session(self):
        """
        Provides a new SQLAlchemy session. Caller is responsible for closing it.
        """
        return self.SessionLocal()
