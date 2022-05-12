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
from datetime import timedelta
from base import logger
from base import Session


class User(Base):
    __tablename__ = "users"
    id = Column(sqa.Integer, primary_key=True)  # telegram id
    timezone = Column(sqa.Float)
    date_joined = Column(sqa.Date)

    def __init__(self, id, timezone):
        self.id = id
        self.timezone = timezone
        today = datetime.datetime.now(utc) + timedelta(hours=self.timezone)
        self.date_joined = today

    def str(self):
        info = f"user {self.id}, joined at {self.date_joined}"
        return info

    def get_habits(self):
        """Returns a list of user's habits."""
        with Session() as s:
            habits = (
                s.query(Habit)
                .filter_by(user=self.id)
                .order_by(Habit.id.desc())
                .with_entities(Habit.name, Habit.id, Habit.user, Habit.method)
                .all()
            )
            return habits

    def habit_name_is_duplicate(self, habit_name):
        lower_cased_name = habit_name.lower()
        with Session() as s:
            habits = s.query(Habit.name).all()
            for habit in habits:
                if lower_cased_name == habit[0].lower():
                    return True
        return False


class Habit(Base):
    __tablename__ = "habits"
    id = Column(sqa.Integer, primary_key=True)
    name = Column(sqa.String(300))
    user = Column(sqa.Integer, ForeignKey("users.id"))
    method = Column(sqa.Integer, ForeignKey("methods.id"))
    date_created = Column(sqa.Date)

    def __init__(self, name, user, method):
        self.name = name
        self.user = user
        self.method = method
        self.date_created = self.today_in_timezone()

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
        today_date = self.today_in_timezone()
        with Session() as s:
            method = s.query(Method).filter_by(id=self.method).one_or_none()
            calculator = method.calculator(
                today_date=today_date,
                records=self.records,
                interval=method.interval,
                duration=method.duration,
                count=method.count,
                specified=method.specified_days,
            )
        return calculator

    def today_in_timezone(self):
        with Session() as s:
            user = s.query(User).filter_by(id=self.user).one_or_none()
        today = datetime.datetime.now(utc) + timedelta(hours=user.timezone)
        return today.date()

    @property
    def total_done_days(self):
        return self.records.count()

    @property
    def done_this_week(self):
        today = self.today_in_timezone()
        week_start = today - timedelta(days=today.isoweekday() - 1)
        count = self.records.filter(Record.date >= week_start).count()
        return count

    @property
    def done_this_month(self):
        today = self.today_in_timezone()
        month_start = today.replace(day=1)
        count = self.records.filter(Record.date >= month_start).count()
        return count

    @property
    def has_logs(self):
        return self.total_done_days > 0

    @property
    def streak(self):
        if self.has_logs:
            calculator = self.get_method_calculator()
            return calculator.streak()
        return 0


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
        ("day", "day"),
        ("week", "week"),
        ("month", "month"),
    ]

    __tablename__ = "methods"
    id = Column(sqa.Integer, primary_key=True)
    type = Column(ChoiceType(TYPES))
    duration = Column(ChoiceType(DURATIONS))
    # comma-separated list of day numbers (either in week, month, or year. in week, monday=1)
    specified = Column(sqa.String(300), nullable=True)
    interval = Column(sqa.Integer, nullable=True)
    count = Column(sqa.Integer, nullable=True)

    def __init__(self, type, duration, *args, **kwargs):
        """
        types: specified, interval, count
        durations: day, week, month
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
            print(f"converted is {self.specified}")

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
            str_list = self.specified.split(",")
            return [int(day) for day in str_list]
        return []

    def convert_specified(self, list_):
        """Converts list of days to a comma seperated string."""
        list_ = [str(day) for day in list_]
        return ",".join(list_)


# --------- Method Calculators ---------


# Durations
day = "day"
week = "week"
month = "month"


class MethodCalculator(ABC):
    def __init__(self, records, today_date, *args, **kwargs):
        self._streak = 0
        self.today = today_date
        self.records = records
        self.oldest_done_date = records[-1].date if records.count() else None
        self.duration_start = None
        self.duration_end = None

    def streak(self):
        pass

    def reminder(self):
        pass

    def is_oldest_duration(self):
        "Returns True if current duration has the oldest dates in records."
        if self.duration_start <= self.oldest_done_date:
            logger.debug("is oldest duration")
        else:
            logger.debug("is not oldest duration")
        return self.duration_start <= self.oldest_done_date

    def go_back_a_duration(self):
        # Start: first day of duration. End: last day of duration.
        self.duration_end = self.duration_start - timedelta(days=1)

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

        if self.is_oldest_duration():
            self.duration_start = self.oldest_done_date
        logger.debug(f"{self.duration_start=},{self.duration_end=}")

    def set_duration_start_end(self):
        """Sets today as last day of duration, and start of week/month as the first day."""
        self.duration_end = self.today

        if self.duration == week:
            self.duration_start = self.duration_end - timedelta(
                days=self.today.isoweekday() - 1
            )
        elif self.duration == month:
            self.duration_start = self.today.replace(day=1)

        else:
            raise TypeError(
                f"duration is wrong. it is {self.duration}, type: {type(self.duration)}"
            )
        logger.debug(f"{self.duration_start=},{self.duration_end=}")


class IntervalCalculator(MethodCalculator):
    def __init__(self, records, today_date, *args, **kwargs):
        self.interval = kwargs.get("interval")
        self.duration = kwargs.get("duration")
        self.done_dates = [record.date for record in records.all()]
        super().__init__(records, today_date)

    def check_date_and_go_one_interval_back(self, date):
        if date in self.done_dates:
            self._streak += 1
            self.check_date_and_go_one_interval_back(
                date - timedelta(days=self.interval)
            )
        return

    def streak(self):
        # Not having a log for today doesn't break the streak. We hope they will log today.
        # So if interval = 1 (everyday), and has a log yesterday, streak will be 1.
        for i in range(self.interval + 1):
            date = self.today - timedelta(days=i)
            if date in self.done_dates:
                self._streak += 1
                self.check_date_and_go_one_interval_back(
                    date - timedelta(days=self.interval)
                )
                return self._streak
        return 0

    def total_loggable_days(self):
        days_passed = (self.today - self.oldest_done_date + timedelta(1)).days
        if days_passed < self.interval:
            return 1
        loggable_days = math.ceil(days_passed / self.interval)
        return loggable_days


class CountCalculator(MethodCalculator):
    def __init__(self, records, today_date, *args, **kwargs):
        self.count = kwargs.get("count")
        self.duration = kwargs.get("duration")
        super().__init__(records, today_date)

    def dones_in_duration(self):
        """Number of done records in the currently checked duration."""
        return self.records.filter(
            self.duration_start <= Record.date, Record.date <= self.duration_end
        ).count()

    def streak(self):
        """Considerations:
        current week/month does NOT break the streak. if it exceeds goal, it adds to streak. but it never breaks it.
        If first week/month's days are less than the goal, it will still add to streak as long as the number of its days
        match the number of records for that week/month.
        """
        if not self.oldest_done_date:
            return 0
        self.set_duration_start_end()
        logger.debug(f"duration start:{self.duration_start} end: {self.duration_end}")
        print(f"{self.dones_in_duration()=}")
        if self.dones_in_duration() >= self.count:
            logger.debug("dones>=count")
            self._streak += 1
        if self.is_oldest_duration():
            return self._streak
        logger.debug(f"streak after current duration: {self._streak}")
        while True:
            self.go_back_a_duration()
            logger.debug(
                f"go back a duration. duration start:{self.duration_start} end: {self.duration_end}"
            )
            if self.is_oldest_duration():
                self._streak += self.oldest_duration_streak()
                return self._streak

            if self.dones_in_duration() >= self.count:
                self._streak += 1

            else:
                return self._streak

    def oldest_duration_streak(self):
        streak = 0
        dones = self.dones_in_duration()
        days = self.days_in_duration()
        if days >= self.count:
            logger.debug("days >= self.count")
            if dones >= self.count:
                logger.debug("dones >= self.count")
                streak = 1
        else:
            logger.debug("days < self.count")
            logger.debug(f"{days=},{dones=}")
            if dones == days:
                logger.debug("days = self.count")
                streak = 1
        logger.debug(f"oldest duration streak is {streak}")
        return streak

    def days_in_duration(self):
        """Number of available days in currently checked duration."""
        return int((self.duration_end - self.duration_start).days) + 1

    def duration_days_equal_or_more_than_count(self):
        return self.days_in_duration() >= self.count

    def total_loggable_days(self):
        loggable_days = 0
        self.set_duration_start_end()
        if self.duration_days_less_than_count():
            loggable_days += self.days_in_duration()
        else:
            loggable_days += self.count
        if self.oldest_done_date >= self.duration_start:
            return loggable_days

        while True:
            self.go_back_a_duration()
            if self.is_oldest_duration():
                self.duration_start = self.oldest_done_date
                if self.duration_days_less_than_count():
                    loggable_days += self.days_in_duration()
                else:
                    loggable_days += self.count
                break
            loggable_days += self.count
        return loggable_days


class SpecifiedCalculator(MethodCalculator):
    def __init__(self, records, today_date, *args, **kwargs):
        self.days = sorted(kwargs.get("specified"), reverse=True)

        self.duration = kwargs.get("duration")
        super().__init__(records, today_date)

    def done_dates_in_duration(self):
        records = self.records.filter(
            self.duration_start <= Record.date, Record.date <= self.duration_end
        )
        return [record.date for record in records]

    @property
    def todays_day_num(self):
        if self.duration == week:
            logger.debug(f"todays_num = {self.today.isoweekday()}")
            return self.today.isoweekday()
        elif self.duration == month:
            logger.debug(f"todays_num = {self.today.day}")
            return self.today.day

    def streak(self):
        """Considerations:
        current week/month does NOT break the streak. if it exceeds goal, it adds to streak. but it never breaks it.
        If some of first week/month's specific days came before user started, they will be ignored. it the rest of
        the days are logged as done, user recieves the streak for that duration.
        """
        if not self.oldest_done_date:
            return 0
        self.set_duration_start_end()
        if max(self.days) <= self.todays_day_num:
            logger.debug("max(self.days) <= self.today.isoweekday()")
            # if its even possible to get a streak using normal methods from current month yet.
            self.set_goal_dates()
            self._streak += self.one_duration_streak()
            logger.debug(f"streak for current duration is {self._streak}")
        if self.is_oldest_duration():
            logger.debug("Current duration is oldest duration")
            return self._streak

        while True:
            self.go_back_a_duration()
            self.set_goal_dates()
            if self.is_oldest_duration():

                self._streak += self.oldest_duration_streak()
                return self._streak
            duration_streak = self.one_duration_streak()
            if duration_streak == 0:
                return self._streak
            self._streak += 1

    def set_goal_dates(self):
        """Converts specified days to date objects in current week/month.
        in case its the oldest duration, it uses first day of the week/month instead of duration start.
        """
        first = self.duration_start
        if self.is_oldest_duration():
            start_days = {
                week: self.duration_end - timedelta(self.duration_end.isoweekday() - 1),
                month: self.duration_end.replace(day=1),
            }
            first = start_days.get(self.duration, None)
        logger.debug(f"{first=}")
        self.goal_dates = [first + timedelta(day - 1) for day in self.days]
        logger.debug(f"goal dates are {self.goal_dates}")

    def one_duration_streak(self):
        """Checks a single duration to see if it can add to streak. returns 0 or 1"""
        logger.debug(f"----Getting one duration streak----")
        done_dates = self.done_dates_in_duration()
        logger.debug(f"{done_dates=}")
        for day in self.goal_dates:
            if day not in done_dates:
                logger.debug(f"goal date {day} is not in done dates, returning 0")
                return 0
            logger.debug(f"goal date {day} is in done dates, continuing")

        return 1

    def oldest_duration_streak(self):
        """If a goal date was smaller than the oldest record available, it will be ignored.
        If all goal dates >= oldest record are marked as done, this duration will get a streak.
        Otherwise, will return zero."""
        logger.debug("------OLDEST DURATION STREAK------")
        done_dates = self.done_dates_in_duration()
        logger.debug(f"{done_dates=}")
        num_goal_dates_logged = 0  # to make sure at least one goal day is done.
        for day in self.goal_dates:
            logger.debug(f"checking goal date {day}")
            if day >= self.duration_start:
                logger.debug(f"goal date >= duration start (oldest record)")
                if day in done_dates:
                    logger.debug(f"goal date is in done dates. adding 1.")
                    num_goal_dates_logged += 1
                else:
                    logger.debug(f"goal date not in done date. returning 0")
                    return 0
            else:
                logger.debug(
                    f"goal date smaller than duration start (oldest record). ignored."
                )
        if num_goal_dates_logged:
            logger.debug(f"{num_goal_dates_logged=}, returning 1 streak")
            return 1

        logger.debug(f"{num_goal_dates_logged=}, returning 0 streak")
        return 0

    def total_loggable_days(self):
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
            if self.is_oldest_duration():
                break
            self.go_back_a_duration()
        return loggable_days

    def loggable_days_in_week(self):
        loggable_days = 0
        while True:
            for day in self.days:
                if self.duration_start.weekday() <= day <= self.duration_end.weekday():
                    loggable_days += 1
            if self.is_oldest_duration():
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
            if self.is_oldest_duration():
                break
            self.go_back_a_duration()

        return loggable_days
