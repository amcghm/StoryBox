from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from reverie.config.config import Config

# Create database engine
engine = create_engine(Config.database_url)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class
Base = declarative_base()

# These Tables need to be imported before initializing the database
from reverie.common.event import Event
from reverie.database.table.persona_table import PersonaTable

# Initialize database
Base.metadata.create_all(bind=engine)

# Database session
db = SessionLocal()
