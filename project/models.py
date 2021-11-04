from base import Base
from sqlalchemy import Column
import sqlalchemy as sqa
from sqlalchemy.sql.schema import ForeignKey
from datetime import date


class User(Base):
    __tablename__ = "users"
    id = Column(sqa.Integer,primary_key=True)
    telegram_id = Column(sqa.Integer, unique=True)
    date_joined = Column(sqa.Date)

    def __init__(self, id):
        self.id = id
        self.date_joined = date.today()

    def str(self):
        info = f"user {self.id}, joined at {self.date_joined}"
        return info


class Habit(Base):
    __tablename__ = "habits"
    id = Column(sqa.Integer, primary_key=True)
    name = Column(sqa.String)
    user = Column(sqa.Integer, ForeignKey("users.id"))
    method_id = Column(sqa.Integer, nullable=True)

    def __init__(self, name, user):
        self.name = name
        self.user = user

    def str(self):
        info = f"habit {self.name}, belonging to {self.user}, with method {self.method_id if self.method_id else 'None' }"
        return info


class Record(Base):
    __tablename__ = "records"
    id = Column(sqa.Integer, primary_key=True)
    user = Column(sqa.Integer, ForeignKey("users.id"))
    habit = Column(sqa.Integer, ForeignKey("habits.id"))
    date = Column(sqa.Date)

    def __init__(self, user, habit, date):
        self.user = user
        self.habit = habit
        self.date = date.today()

    def str(self):
        info = f"habit {self.name}, logged by {self.user} on {self.date}"
        return info


class MethodBase:
    def __init__(self, name):
        self.name = name

    def calc_streak(self):
        pass
