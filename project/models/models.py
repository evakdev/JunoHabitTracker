from base import Base
from sqlalchemy import Column
import sqlalchemy as sqa
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.orm import load_only
from datetime import date
from base import Session


class User(Base):
    __tablename__ = "users"
    tid = Column(sqa.Integer, primary_key=True) #telegram id
    date_joined = Column(sqa.Date)

    def __init__(self, id):
        self.id = id
        self.date_joined = date.today()

    def str(self):
        info = f"user {self.id}, joined at {self.date_joined}"
        return info

    @property
    def habits(self):
        """Returns user's habits' names. 
        ATTENTION: this does not return objects.
        """

        with Session() as s:
            habits = s.query(Habit).filter_by(user=self.id).order_by(Habit.name)
            return habits.query(Habit.name)

class Habit(Base):
    __tablename__ = "habits"
    id = Column(sqa.Integer, primary_key=True)
    name = Column(sqa.String)
    user = Column(sqa.Integer, ForeignKey("users.id"))
    method = Column(sqa.Integer, nullable=True)

    def __init__(self, name, user):
        self.name = name
        self.user = user

    def str(self):
        info = f"habit {self.name}, belonging to {self.user}, with method {self.method if self.method else 'None' }"
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
        self.streak = None

    def calc_streak(self, user, habit):
        pass

    def get_records(self, user, habit):
        with Session() as s:
            records = (
                s.query(Record)
                .filter_by(user=user.id, habit=habit.id)
                .order_by(Record.date.desc)
                .options(load_only("date"))
            )
            return records
