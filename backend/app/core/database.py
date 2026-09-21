from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# External Databases
cid_engine = create_engine(settings.CID_DB_URL, pool_pre_ping=True) if settings.CID_DB_URL else None
monitoreo_engine = create_engine(settings.MONITOREO_DB_URL, pool_pre_ping=True) if settings.MONITOREO_DB_URL else None
billetaje_engine = create_engine(settings.BILLETAJE_DB_URL, pool_pre_ping=True) if settings.BILLETAJE_DB_URL else None

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_cid_db():
    if not cid_engine: return None
    db = sessionmaker(autocommit=False, autoflush=False, bind=cid_engine)()
    try:
        yield db
    finally:
        db.close()

def get_monitoreo_db():
    if not monitoreo_engine: return None
    db = sessionmaker(autocommit=False, autoflush=False, bind=monitoreo_engine)()
    try:
        yield db
    finally:
        db.close()

def get_billetaje_db():
    if not billetaje_engine: return None
    db = sessionmaker(autocommit=False, autoflush=False, bind=billetaje_engine)()
    try:
        yield db
    finally:
        db.close()
