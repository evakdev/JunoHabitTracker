import math

from pytz import utc
from base import Base
from sqlalchemy import Column
import sqlalchemy as sqa
from sqlalchemy.sql.schema import ForeignKey
import datetime
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
                .with_entities(Habit.name, Habit.id, Habit.user, Habit.method)
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
        self.date_created = self.today_in_timezone(user)

    def str(self):
        info = f"habit {self.name}, belonging to {self.user}, with method {self.method if self.method else 'None' }"
        return info

    @property
    def records(self):
        """Returns a query of habit's records, the first being the most recent."""
        with Session() as s:
            records = (
                s.query(Record).filter_by(habit=self.id).order_by(Record.date.desc())
            )
            return records

    def get_method_calculator(self):
        with Session() as s:
            method = s.query(Method).filter_by(id=self.method).one_or_none()
            calculator = method.calculator(
                self.records,
                interval=method.interval,
                duration=method.duration,
                count=method.count,
                specified=method.specified,
            )
        return calculator

    def today_in_timezone(self, user_id):
        with Session() as s:
            user = s.query(User).filter_by(id=user_id).one_or_none()
        today = datetime.datetime.now(utc) + timedelta(hours=user.timezone)
        return today.date()

    @property
    def streak(self):
        calculator = self.get_method_calculator()
        return calculator.streak()

    @property
    def total_done_days(self):
        return self.records.count()

    @property
    def total_loggable_days(self):
        today = self.today_in_timezone(self.user)
        return self.get_method_calculator().total_loggable_days(today)


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


# --------- Method Calculators ---------


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
        if self.is_first_duration():
            self.duration_start = self.first_date_ever

    def set_duration_start_end(self):

        if self.duration == week:
            self.duration_start = self.today - timedelta(days=self.today.isoweekday())
        elif self.duration == month:
            self.duration_start = self.today.replace(day=1)

        self.duration_end = self.today + timedelta(days=1)


class IntervalCalculator(MethodCalculator):
    def __init__(self, records, *args, **kwargs):
        self.interval = kwargs.get("interval")
        self.duration = kwargs.get("duration")
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

    def total_loggable_days(self, today_date):
        days_passed = (today_date - self.first_date_ever + timedelta(1)).days
        if days_passed < self.interval:
            return 1
        loggable_days = math.ceil(days_passed / self.interval)
        return loggable_days


class CountCalculator(MethodCalculator):
    def __init__(self, records, *args, **kwargs):
        self.count = kwargs.get("count")
        self.duration = kwargs.get("duration")
        super().__init__(records)

    def streak(self):
        self.set_duration_start_end()
        self._streak += self.dones_in_duration().count()

        while True:
            self.go_back_a_duration()
            done_count = self.dones_in_duration().count()

            if self.is_first_duration():
                if self.duration_days_less_than_count():
                    return self._streak
                self._streak += done_count
                continue
            elif done_count < self.count:
                return self._streak
            self._streak += done_count

    def days_in_duration(self):
        return int(self.duration_end - self.duration_start)

    def duration_days_less_than_count(self):
        return self.days_in_duration() < self.count

    def total_loggable_days(self, today_date):
        self.today = today_date  # to be timezone compatible
        loggable_days = 0
        self.set_duration_start_end()
        if self.duration_days_less_than_count():
            loggable_days += self.days_in_duration()
        else:
            loggable_days += self.count
        if self.first_date_ever >= self.duration_start:
            return loggable_days

        while True:
            self.go_back_a_duration()
            if self.is_first_duration():
                self.duration_start = self.first_date_ever
                if self.duration_days_less_than_count():
                    loggable_days += self.days_in_duration()
                else:
                    loggable_days += self.count
                break
            loggable_days += self.count
        return loggable_days


class SpecifiedCalculator(MethodCalculator):
    def __init__(self, records, *args, **kwargs):
        self.days = kwargs.get("specified").sort(reverse=True)
        self.duration = kwargs.get("duration")
        super().__init__(records)

    def streak(self):
        self.set_duration_start_end()
        while True:
            self.set_duration_dates()
            done = self.records.filter(Record.date in self.duration_dates)
            done_count = done.count()
            if done_count != len(self.days) or self.is_first_duration():
                self._streak += self.one_duration_streak()
                return self._streak
            else:
                self._streak += done_count
                self.go_back_a_duration()

    def set_duration_dates(self):
        self.duration_dates = [
            self.duration_start + timedelta(day - 1) for day in self.days
        ]

    def one_duration_streak(self, done_records):
        duration_streak = 0
        for day in self.duration_dates:
            day_record = done_records.filter(Record.date == day).one_or_none()
            if not day_record:
                return duration_streak
            duration_streak += 1
        return duration_streak

    def total_loggable_days(self, today_date):
        self.today = today_date
        loggable_days = 0
        normal_days = self.days
        if not self.days_are_normal:
            normal_days = [day for day in self.days if day not in [29, 30, 31]]
            loggable_days = self.count_loggable_days_in_weird_days()
        self.set_duration_start_end()
        if self.duration == week:
            loggable_days += self.loggable_days_in_week()
        else:
            loggable_days += self.loggable_days_in_month(normal_days)
        return loggable_days

    def loggable_days_in_month(self, normal_days):
        loggable_days = 0
        while True:
            for day in normal_days:
                if self.duration_start.day <= day <= self.duration_end.day:
                    loggable_days += 1
            if self.is_first_duration():
                break
            self.go_back_a_duration()
        return loggable_days

    def loggable_days_in_week(self):
        loggable_days = 0
        while True:
            for day in self.days:
                if self.duration_start.weekday() <= day <= self.duration_end.weekday():
                    loggable_days += 1
            if self.is_first_duration():
                break
            self.go_back_a_duration()
        return loggable_days

    def days_are_normal(self):
        "To figure out if days 29 to 31 of months are in chosen days."
        weird_days = [29, 30, 31]
        if self.duration == week:
            return True
        for day in weird_days:
            if day in self.days:
                return False
        return True

    def date_is_valid(self, year, month, day):
        try:
            date = datetime(year, month, day)
            return True
        except ValueError:
            return False

    def count_loggable_days_in_weird_days(self):
        loggable_days = 0
        weird_days = [day if day in self.days else None for day in [29, 30, 31]]
        self.set_duration_start_end()
        while True:

            for day in weird_days:
                y, m, d = self.duration_start.year, self.duration_start.month, day
                if self.date_is_valid(y, m, d):
                    if day >= self.duration_start.day and day <= self.duration_end.day:
                        loggable_days += 1
            if self.is_first_duration():
                break
            self.go_back_a_duration()

        return loggable_days
