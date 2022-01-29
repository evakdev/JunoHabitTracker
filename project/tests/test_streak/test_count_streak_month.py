import datetime

from sqlalchemy.sql.expression import or_
from base import Session
from models.models import Habit, Record, Method, User
from unittest import TestCase
import unittest


class TestCountStreakBase(TestCase):
    def setUp(self) -> None:
        self.user_id = 1
        self.today = datetime.date(2021, 12, 25)

    def get_calculator(self):
        with Session() as s:
            habit = s.query(Habit).filter_by(user=self.user_id).one()
            method = s.query(Method).filter_by(id=habit.method).one()
            calculator = method.calculator(
                records=habit.records,
                today_date=self.today,
                count=method.count,
                duration=method.duration,
            )
            return calculator

    def tearDown(self) -> None:

        with Session() as s:
            records = s.query(Record).filter_by(user=self.user_id).delete()
            habit = s.query(Habit).filter_by(user=self.user_id)
            method_id = habit[0].method
            habit.delete()
            method = s.query(Method).filter_by(id=method_id).delete()
            user = s.query(User).filter_by(id=self.user_id).delete()
            s.commit()


class TestNoRecordsExist(TestCountStreakBase):
    def setUp(self) -> None:
        self.user_id = 1
        self.today = datetime.date(2021, 12, 25)
        with Session(expire_on_commit=False) as s:
            user = User(self.user_id, 0)
            duration = "month"
            method = Method(type="count", duration=duration, count=4)
            s.add_all([user, method])
            s.commit()
            self.habit = Habit("count_habit_month_4days", user.id, method.id)
            s.add(self.habit)
            s.commit()

    def test_no_records_exist(self):
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 0)


class TestThreeDurationsOldestFull(TestCountStreakBase):
    def setUp(self) -> None:
        self.user_id = 1
        self.today = datetime.date(2021, 12, 25)
        with Session(expire_on_commit=False) as s:
            user = User(self.user_id, 0)
            duration = "month"
            method = Method(type="count", duration=duration, count=4)
            s.add_all([user, method])
            s.commit()
            self.habit = Habit("count_habit_month_4days", user.id, method.id)
            s.add(self.habit)
            s.commit()
            self.records_oldest = [
                Record(user.id, self.habit.id, datetime.date(2021, 10, 13)),
                Record(user.id, self.habit.id, datetime.date(2021, 10, 16)),
                Record(user.id, self.habit.id, datetime.date(2021, 10, 18)),
                Record(user.id, self.habit.id, datetime.date(2021, 10, 19)),
            ]
            self.records_middle = [
                Record(user.id, self.habit.id, datetime.date(2021, 11, 21)),
                Record(user.id, self.habit.id, datetime.date(2021, 11, 28)),
                Record(user.id, self.habit.id, datetime.date(2021, 11, 29)),
                Record(user.id, self.habit.id, datetime.date(2021, 11, 30)),
            ]
            self.records_current = [
                Record(user.id, self.habit.id, datetime.date(2021, 12, 7)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 8)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 9)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 10)),
            ]

            s.add_all(self.records_oldest + self.records_middle + self.records_current)
            s.commit()

    def test_all_full(self):
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 3)

    def test_all_half(self):
        with Session() as s:
            s.query(Record).filter(
                Record.user == self.user_id,
                or_(
                    Record.date == self.records_oldest[2].date,
                    Record.date == self.records_middle[2].date,
                    Record.date == self.records_current[2].date,
                ),
            ).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 0)

    def test_oldest_half_middle_full_current_full(self):
        with Session() as s:
            s.query(Record).filter(
                Record.user == self.user_id,
                Record.date == self.records_oldest[1].date,
            ).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 2)

    def test_oldest_half_middle_half_current_full(self):
        with Session() as s:
            s.query(Record).filter(
                Record.user == self.user_id,
                or_(
                    Record.date == self.records_oldest[1].date,
                    Record.date == self.records_middle[1].date,
                ),
            ).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)

    def test_middle_half_oldest_full_current_full(self):
        with Session() as s:
            s.query(Record).filter(
                Record.user == self.user_id,
                Record.date == self.records_middle[1].date,
            ).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)

    def test_middle_none_oldest_full_current_full(self):
        with Session() as s:
            s.query(Record).filter(
                Record.user == self.user_id,
                Record.date > self.records_oldest[-1].date,
                Record.date < self.records_current[0].date,
            ).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)

    def test_middle_half_current_half_oldest_full(self):
        with Session() as s:
            s.query(Record).filter(
                Record.user == self.user_id,
                or_(
                    Record.date == self.records_current[1].date,
                    Record.date == self.records_middle[1].date,
                ),
            ).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 0)

    def test_current_half_oldest_full_middle_full(self):
        with Session() as s:
            s.query(Record).filter(
                Record.user == self.user_id,
                Record.date == self.records_current[1].date,
            ).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 2)

    def test_current_none_oldest_full_middle_full(self):
        with Session() as s:
            s.query(Record).filter(
                Record.user == self.user_id,
                Record.date > self.records_middle[-1].date,
            ).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 2)

    def test_current_half_oldest_half_middle_full(self):
        with Session() as s:
            s.query(Record).filter(
                Record.user == self.user_id,
                or_(
                    Record.date == self.records_current[1].date,
                    Record.date == self.records_oldest[1].date,
                ),
            ).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)

    def test_oldest_more_than_count_middle_full_current_full(self):
        with Session() as s:
            record = Record(self.user_id, self.habit.id, datetime.date(2021, 10, 15))
            s.add(record)
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 3)

    def test_middle_more_than_count_oldest_full_current_full(self):
        with Session() as s:
            record = Record(self.user_id, self.habit.id, datetime.date(2021, 11, 23))
            s.add(record)
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 3)

    def test_current_more_than_count_oldest_full_middle_full(self):
        with Session() as s:
            record = Record(self.user_id, self.habit.id, datetime.date(2021, 12, 15))
            s.add(record)
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 3)


class TestOldestDurationLessDaysThanCount(TestCountStreakBase):
    def setUp(self) -> None:

        self.user_id = 1
        self.today = datetime.date(2021, 12, 25)

        with Session(expire_on_commit=False) as s:
            user = User(self.user_id, 0)
            duration = "month"
            method = Method(type="count", duration=duration, count=4)
            s.add_all([user, method])
            s.commit()
            self.habit = Habit("count_habit_month_4days", user.id, method.id)
            s.add(self.habit)
            s.commit()
            self.records_oldest = [
                Record(user.id, self.habit.id, datetime.date(2021, 11, 28)),
                Record(user.id, self.habit.id, datetime.date(2021, 11, 29)),
                Record(user.id, self.habit.id, datetime.date(2021, 11, 30)),
            ]
            self.records_current = [
                Record(user.id, self.habit.id, datetime.date(2021, 12, 17))
            ]

            s.add_all(self.records_oldest + self.records_current)
            s.commit()

    def test_oldest_full_current_half(self):
        with Session() as s:
            calculator = self.get_calculator()
            self.assertEqual(calculator.streak(), 1)

    def test_oldest_half_current_half(self):
        with Session() as s:
            s.query(Record).filter_by(
                user=self.user_id, date=self.records_oldest[1].date
            ).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 0)

    def test_oldest_none_current_half(self):
        with Session() as s:
            s.query(Record).filter(
                Record.user == self.user_id, Record.date < self.records_current[0].date
            ).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 0)

    def test_oldest_full_current_full(self):
        with Session() as s:
            records = [
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 18)),
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 20)),
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 23)),
            ]

            s.add_all(records)
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 2)

    def test_oldest_full_current_none(self):
        with Session() as s:
            s.query(Record).filter(
                Record.user == self.user_id, Record.date > self.records_oldest[-1].date
            ).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)


class TestOldestDurationEqualDaysToCount(TestCountStreakBase):
    def setUp(self) -> None:

        self.user_id = 1
        self.today = datetime.date(2021, 12, 25)

        with Session(expire_on_commit=False) as s:

            user = User(self.user_id, 0)
            duration = "month"
            method = Method(type="count", duration=duration, count=4)
            s.add_all([user, method])
            s.commit()
            self.habit = Habit("count_habit_month_4days", user.id, method.id)
            s.add(self.habit)
            s.commit()

            self.records_oldest = [
                Record(user.id, self.habit.id, datetime.date(2021, 11, 27)),
                Record(user.id, self.habit.id, datetime.date(2021, 11, 28)),
                Record(user.id, self.habit.id, datetime.date(2021, 11, 29)),
                Record(user.id, self.habit.id, datetime.date(2021, 11, 30)),
            ]
            self.records_current = [
                Record(user.id, self.habit.id, datetime.date(2021, 12, 17))
            ]

            s.add_all(self.records_current + self.records_oldest)
            s.commit()

    def test_oldest_full_current_half(self):
        with Session() as s:
            calculator = self.get_calculator()
            self.assertEqual(calculator.streak(), 1)

    def test_oldest_half_current_half(self):
        with Session() as s:
            s.query(Record).filter_by(
                user=self.user_id, date=self.records_oldest[1].date
            ).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 0)

    def test_oldest_none_current_half(self):
        with Session() as s:
            s.query(Record).filter(
                Record.user == self.user_id, Record.date < self.records_current[0].date
            ).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 0)

    def test_oldest_full_current_full(self):
        with Session() as s:
            records = [
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 18)),
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 20)),
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 23)),
            ]

            s.add_all(records)
            s.commit()

        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 2)

    def test_oldest_full_current_none(self):
        with Session() as s:
            s.query(Record).filter(
                Record.user == self.user_id, Record.date > self.records_oldest[-1].date
            ).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)


class TestOldestDurationMoreDaysThanCount(TestCountStreakBase):
    def setUp(self) -> None:

        self.user_id = 1
        self.today = datetime.date(2021, 12, 25)

        with Session(expire_on_commit=False) as s:

            user = User(self.user_id, 0)
            duration = "month"
            method = Method(type="count", duration=duration, count=4)
            s.add_all([user, method])
            s.commit()
            self.habit = Habit("count_habit_month_4days", user.id, method.id)
            s.add(self.habit)
            s.commit()
            self.records_oldest = [
                Record(user.id, self.habit.id, datetime.date(2021, 11, 22)),
                Record(user.id, self.habit.id, datetime.date(2021, 11, 24)),
                Record(user.id, self.habit.id, datetime.date(2021, 11, 25)),
                Record(user.id, self.habit.id, datetime.date(2021, 11, 26)),
            ]
            self.records_current = [
                Record(user.id, self.habit.id, datetime.date(2021, 12, 17))
            ]

            s.add_all(self.records_oldest + self.records_current)
            s.commit()

    def test_oldest_full_current_half(self):
        with Session() as s:
            calculator = self.get_calculator()
            self.assertEqual(calculator.streak(), 1)

    def test_oldest_half_current_half(self):
        with Session() as s:
            s.query(Record).filter_by(
                user=self.user_id, date=self.records_oldest[1].date
            ).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 0)

    def test_oldest_none_current_half(self):
        with Session() as s:
            s.query(Record).filter(
                Record.user == self.user_id, Record.date < self.records_current[0].date
            ).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 0)

    def test_oldest_full_current_full(self):
        with Session() as s:
            records = [
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 18)),
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 20)),
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 22)),
            ]

            s.add_all(records)
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 2)

    def test_oldest_full_current_none(self):
        with Session() as s:
            s.query(Record).filter(
                Record.user == self.user_id, Record.date > self.records_oldest[-1].date
            ).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)


class TestCurrentAndMiddleDurationsHaveNoRecords(TestCountStreakBase):
    def setUp(self) -> None:

        self.user_id = 1
        self.today = datetime.date(2021, 12, 25)

        with Session(expire_on_commit=False) as s:
            user = User(self.user_id, 0)
            duration = "month"
            method = Method(type="count", duration=duration, count=4)
            s.add_all([user, method])
            s.commit()
            self.habit = Habit("count_habit_month_4days", user.id, method.id)
            s.add(self.habit)
            s.commit()

            self.records_oldest = [
                Record(user.id, self.habit.id, datetime.date(2021, 10, 6)),
                Record(user.id, self.habit.id, datetime.date(2021, 10, 10)),
                Record(user.id, self.habit.id, datetime.date(2021, 10, 18)),
                Record(user.id, self.habit.id, datetime.date(2021, 10, 19)),
            ]
            s.add_all(self.records_oldest)
            s.commit()

    def test_oldest_full(self):
        with Session() as s:
            calculator = self.get_calculator()
            self.assertEqual(calculator.streak(), 0)

    def test_oldest_half(self):
        with Session() as s:
            s.query(Record).filter_by(
                user=self.user_id, date=self.records_oldest[1].date
            ).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 0)


class OldestDurationisCurrentDuration(TestCountStreakBase):
    def setUp(self) -> None:
        self.user_id = 1
        self.today = datetime.date(2021, 12, 25)

        with Session(expire_on_commit=False) as s:
            user = User(self.user_id, 0)
            duration = "month"
            method = Method(type="count", duration=duration, count=4)
            s.add_all([user, method])
            s.commit()
            self.habit = Habit("count_habit_month_4days", user.id, method.id)
            s.add(self.habit)
            s.commit()
            self.records = [
                Record(user.id, self.habit.id, datetime.date(2021, 12, 7)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 18)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 19)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 25)),
            ]

            s.add_all(self.records)
            s.commit()

    def test_counts_today(self):
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)

    def test_duration_full(self):
        with Session() as s:
            calculator = self.get_calculator()
            self.assertEqual(calculator.streak(), 1)

    def test_duration_half(self):
        with Session() as s:
            s.query(Record).filter_by(
                user=self.user_id, date=self.records[1].date
            ).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 0)

    def test_duration_none(self):
        with Session() as s:
            s.query(Record).filter_by(user=self.user_id).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 0)


class TestCurrentDurationLessOrEqualDaysThanCount(TestCountStreakBase):
    def setUp(self) -> None:
        self.user_id = 1
        self.today = datetime.date(2021, 12, 4)
        with Session(expire_on_commit=False) as s:
            user = User(self.user_id, 0)
            duration = "month"
            method = Method(type="count", duration=duration, count=4)
            s.add_all([user, method])
            s.commit()
            self.habit = Habit("count_habit_month_4days", user.id, method.id)
            s.add(self.habit)
            s.commit()

            self.records_oldest = [
                Record(user.id, self.habit.id, datetime.date(2021, 11, 20)),
                Record(user.id, self.habit.id, datetime.date(2021, 11, 22)),
                Record(user.id, self.habit.id, datetime.date(2021, 11, 24)),
                Record(user.id, self.habit.id, datetime.date(2021, 11, 25)),
            ]
            self.records_current = [
                Record(user.id, self.habit.id, datetime.date(2021, 12, 1)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 2)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 3)),
            ]

            s.add_all(self.records_oldest + self.records_current)
            s.commit()

    def test_current_equal_days_to_count_but_half_full_oldest_full(self):
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)

    def test_current_equal_days_to_count_current_full_oldest_full(self):
        with Session() as s:
            record = Record(self.user_id, self.habit.id, datetime.date(2021, 12, 4))
            s.add(record)
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 2)

    def test_current_less_days_than_count_current_full_oldest_full(self):

        self.today = datetime.date(2021, 12, 3)
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)

    def test_current_less_days_than_count_half_full_oldest_full(self):
        with Session() as s:
            s.query(Record).filter_by(
                user=self.user_id, date=self.records_current[-1].date
            ).delete()
            self.today = datetime.date(2021, 12, 3)
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)


if __name__ == "__main__":
    unittest.main()
