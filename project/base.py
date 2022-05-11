from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from telegram.ext import Updater
from sqlalchemy.ext.declarative import declarative_base

import logging


# SQLAlchemy
engine = create_engine(db_url, echo=False)
Session = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()

# Telegram
updater = Updater(token=token)
dispatcher = updater.dispatcher


# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
