from base import Base
from sqlalchemy import Column
import sqlalchemy as sqa
from sqlalchemy.sql.schema import ForeignKey


class User(Base):
    __tablename__ = "users"
    id = Column(sqa.Integer, primary_key=True)
    date_joined = Column(sqa.Date)


class Habit(Base):
    __tablename__ = "habits"
    id = Column(sqa.Integer, primary_key=True)
    name = Column(sqa.String)
    user = Column(sqa.Integer, ForeignKey("users.id"))
    method_id = Column(sqa.Integer)


class Record(Base):
    __tablename__ = "records"
    id = Column(sqa.Integer, primary_key=True)
    user = Column(sqa.Integer, ForeignKey("users.id"))
    habit = Column(sqa.Integer, ForeignKey("habits.id"))


class MethodBase:
    def __init__(self, name):
        self.name = None

    def calc_streak(self):
        pass
