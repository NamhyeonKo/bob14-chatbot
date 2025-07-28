from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from app.core.config import conf

# Get database configuration
db_config = conf['database']

# Database connection string
DB_CONN = f'mysql+pymysql://{db_config["user"]}:{db_config["password"]}@{db_config["host"]}:{db_config["port"]}/{db_config["database"]}'

# Create declarative base
Base = declarative_base()

class Database:
    def __init__(self):
        self.engine = create_engine(
            DB_CONN,
            pool_pre_ping=True,
            pool_size=20,
            max_overflow=0,
            pool_recycle=3600,
            connect_args={'connect_timeout': 10}
        )
        self.Session = scoped_session(
            sessionmaker(
                bind=self.engine,
                autoflush=False,
                autocommit=False
            )
        )

    def get_session(self):
        db = self.Session()
        try:
            yield db
        finally:
            db.close()

db = Database()
