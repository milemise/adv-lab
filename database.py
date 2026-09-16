from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL


# ==========================================================
# MOTOR DE BASE DE DATOS
# ==========================================================

engine = create_engine(

    DATABASE_URL,

    connect_args={

        "check_same_thread": False

    }

)


# ==========================================================
# SESIONES
# ==========================================================

SessionLocal = sessionmaker(

    autocommit=False,

    autoflush=False,

    bind=engine

)


# ==========================================================
# BASE
# ==========================================================

Base = declarative_base()


# ==========================================================
# DEPENDENCIA FASTAPI
# ==========================================================

def get_db():

    db = SessionLocal()

    try:

        yield db

    finally:

        db.close()