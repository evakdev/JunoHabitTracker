from base import Base
from sqlalchemy import Column
import sqlalchemy as sqa
from sqlalchemy.sql.schema import ForeignKey
from datetime import date
from base import Session
from sqlalchemy_utils.types.choice import ChoiceType
from abc import ABC
from datetime import timedelta, date

from base import Session


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

    def get_habits(self):
        """Returns a list of user's habits' names.
        ATTENTION: this does not return objects.
        """
        with Session() as s:
            habits = (
                s.query(Habit)
                .filter_by(user=self.id)
                .order_by(Habit.id.desc())
                .with_entities(Habit.name, Habit.id, Habit.user)
                .all()
            )
            return habits


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

    @property
    def records(self):
        """Returns a query of habit's records."""
        with Session() as s:
            records = (
                s.query(Record).filter_by(habit=self.id).order_by(Record.date.desc())
            )
            return records

    @property
    def streak(self):
        with Session() as s:
            method = s.query(Method).filter_by(id=self.method).one_or_none()
            calculator = method.calculator(
                self.records,
                interval=method.interval,
                duration=method.duration,
                count=method.count,
                specified=method.specified,
        )
        return calculator.streak()


class Record(Base):
    __tablename__ = "records"
    id = Column(sqa.Integer, primary_key=True)
    user = Column(sqa.Integer, ForeignKey("users.id"))
    habit = Column(sqa.Integer, ForeignKey("habits.id"))
    date = Column(sqa.Date)

    def __init__(self, user, habit, date):
        self.user = user
        self.habit = habit
        self.date = date

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
        self.interval = kwargs.get("interval")
        self.count = kwargs.get("count")
        if kwargs.get("specified"):
            self.specified = self.convert_specified(kwargs.get("specified"))

    @property
    def calculator(self):
        method_calculators = {
            "interval": IntervalCalculator,
            "count": CountCalculator,
            "specified": SpecifiedCalculator,
        }
        return method_calculators.get(self.type)

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


####### Method Calculators


# Durations
week = "week"
month = "month"
year = "year"


class MethodCalculator(ABC):
    def __init__(self, records, *args, **kwargs):
        self._streak = 0
        self.today = date.today()
        self.records = records
        self.first_date_ever = records[-1].date
        self.duration_start = None
        self.duration_end = None

    def streak(self):
        pass

    def reminder(self):
        pass

    def is_first_duration(self):
        return self.duration_start < self.first_date_ever

    def dones_in_duration(self):
        return self.records.filter(
            self.duration_start <= Record.date < self.duration_end
        )

    def go_back_a_duration(self):
        self.duration_end = self.duration_start

        if self.duration == week:
            self.duration_start -= timedelta(days=7)

        elif self.duration == month:
            if self.duration_start.month == 1:
                self.duration_start = self.duration_start.replace(
                    year=self.duration_start.year - 1, month=12
                )
            else:
                self.duration_start = self.duration_start.replace(
                    month=self.duration_start.month - 1
                )

    def set_duration_start_end(self):
       
        if self.duration == week:
            self.duration_start = self.today - timedelta(days=self.today.isoweekday())
        elif self.duration == month:
            self.duration_start = self.today.replace(day=1)

        self.duration_end = self.today + timedelta(days=1)


class IntervalCalculator(MethodCalculator):
    def __init__(self, records, *args, **kwargs):
        self.interval = kwargs.get('interval')
        self.duration = kwargs.get('duration')
        super().__init__(records)

    def streak(self):
        records = self.records.all()
        
        if len(records) == 0:
            return 0

        last_date = records[0].date
        if self.streak_is_broken(last_date):
            return 0

        for record in records:
            if record.date - last_date <= timedelta(days=self.interval):
                self._streak += 1
                last_date = record.date
            else:
                break
        return self._streak

    def streak_is_broken(self, last_date):
        print(f"{last_date=},{self.interval}")
        if self.today - last_date > timedelta(days=self.interval):
            return True


class CountCalculator(MethodCalculator):
    def __init__(self, records, *args, **kwargs):
        self.count = kwargs.get('count')
        self.duration = kwargs.get('duration')
        super().__init__(records)

    def streak(self):
        self.set_duration_start_end()
        self._streak += self.dones_in_duration().count()

        while True:
            self.go_back_a_duration()
            done_count = self.dones_in_duration().count()

            if self.is_first_duration():
                if self.available_days_less_than_count():
                    return self._streak
                self._streak += done_count
                continue
            elif done_count < self.count:
                return self._streak
            self._streak += done_count

    def available_days_less_than_count(self):
        days_in_duration = int(self.duration_end - self.duration_start)
        return days_in_duration < self.count


class SpecifiedCalculator(MethodCalculator):
    def __init__(self, records, *args, **kwargs):
        self.days = kwargs.get('specified').sort(reverse=True)
        self.duration = kwargs.get('duration')
        super().__init__(records)

    def streak(self):
        self.set_duration_start_end()
        while True:
            self.set_duration_dates()
            done = self.records.filter(Record.date in self.duration_dates)
            done_count = done.count()
            if (done_count != len(self.days)
                or self.is_first_duration()):
                self._streak+=self.one_duration_streak()
                return self._streak
            else:
                self._streak += done_count
                self.go_back_a_duration()

    def set_duration_dates(self):
        self.duration_dates = [self.duration_start + timedelta(day - 1) for day in self.days
            ]
    def one_duration_streak(self,done_records):
        duration_streak = 0
        for day in self.duration_dates:
            day_record = done_records.filter(Record.date == day).one_or_none()
            if not day_record:
                return duration_streak
            duration_streak += 1
        return duration_streak


