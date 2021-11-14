from base import Base
from sqlalchemy import Column
import sqlalchemy as sqa
from sqlalchemy.sql.schema import ForeignKey
from datetime import date
from base import Session
from sqlalchemy_utils.types.choice import ChoiceType


class User(Base):
    __tablename__ = "users"
    id = Column(sqa.Integer, primary_key=True)  # telegram id
    timezone = Column(sqa.Float)
    date_joined = Column(sqa.Date)

    def __init__(self, id, timezone):
        self.id = id
        self.timezone = timezone
        self.date_joined = date.today()

    def str(self):
        info = f"user {self.id}, joined at {self.date_joined}"
        return info

    @property
    def habits(self):
        """Returns a list of user's habits' names.
        ATTENTION: this does not return objects.
        """
        with Session() as s:
            habits = (
                s.query(Habit)
                .filter_by(user=self.id)
                .order_by(Habit.name)
                .with_entities(Habit.name)
            )
            names = [habit.name for habit in habits]
            return names


class Habit(Base):
    __tablename__ = "habits"
    id = Column(sqa.Integer, primary_key=True)
    name = Column(sqa.String)
    user = Column(sqa.Integer, ForeignKey("users.id"))
    method = Column(sqa.Integer, ForeignKey("methods.id"), nullable=True)
    date_created = Column(sqa.Date)

    def __init__(self, name, user):
        self.name = name
        self.user = user
        self.date_created = date.today()

    def str(self):
        info = f"habit {self.name}, belonging to {self.user}, with method {self.method if self.method else 'None' }"
        return info

    def records(self):
        """Returns a query of habit's records."""
        with Session() as s:
            records = (
                s.query(Record).filter_by(habit=self.id).order_by(Record.date.desc())
            )
            return records


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


class Method(Base):
    TYPES = [
        ("specified", "Specified Days"),
        ("interval", "Interval"),
        ("count", "Count"),
    ]
    DURATIONS = [
        ("week", "Week"),
        ("month", "Month"),
        ("year", "Year"),
    ]

    __tablename__ = "methods"
    id = Column(sqa.Integer, primary_key=True)
    type = Column(ChoiceType(TYPES))
    duration = Column(ChoiceType(DURATIONS))
    # comma-separated list of day numbers (either in week, month, or year, week starting monday)
    specified = Column(sqa.String, nullable=True)
    interval = Column(sqa.Integer, nullable=True)
    count = Column(sqa.Integer, nullable=True)

    def __init__(self, type, duration, *args, **kwargs):
        """ 
        types: specified, interval, count
        durations: week, month, year
        for type interval: add interval kw
        for type specified: add specified
        for type count: add count

        """
        self.type = type
        self.duration = duration
        self.interval = kwargs.get('interval')
        self.count = kwargs.get('count')
        if kwargs.get('specified'):
            self.specified = self.convert_specified(kwargs.get('specified'))

    @property
    def specified_days(self):
        """Converts comma seperated string of days to a list of integars."""
        if self.specified:
            return [int(day) for day in self.specified.split(",")]
        return []

    def convert_specified(self, list_):
        """Converts list of days to a comma seperated string."""
        list_ = [str(day) for day in list_]
        return ",".join(list_)