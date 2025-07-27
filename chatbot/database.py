""" Database connection and session management. """
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from fastapi import FastAPI
from fastapi.logger import logger

from config import conf

# Create declarative base
Base = declarative_base()

# Get database configuration
db_config = conf['database']

# Database connection string
DB_CONN = f'mysql+pymysql://{db_config["user"]}:{db_config["password"]}@{db_config["host"]}:{db_config["port"]}/{db_config["database"]}'

class SQLAlchemy():
            
    def __init__(self):
        logger.info(f"Connecting to database: {DB_CONN}")
        try:
            self.engine = create_engine(DB_CONN, pool_pre_ping=True, pool_size=20, max_overflow=0, pool_recycle=3600, connect_args={'connect_timeout': 10})
            self.Session = scoped_session(sessionmaker(bind=self.engine, autoflush=False, autocommit=False))
            logger.info("Database connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")

    def get_session(self):
        db = self.Session()
        try:
            yield db
        finally:
            db.close()

db = SQLAlchemy()

# Export all for other modules
__all__ = ['db', 'Base']