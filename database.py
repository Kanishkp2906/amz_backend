from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from config import DB_URL

engine = create_engine(DB_URL, pool_pre_ping=True)
Sessionlocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()

def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()