from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from config import db

engine = create_engine(db, echo=False)
Session = sessionmaker(bind=engine)
Base = declarative_base()
