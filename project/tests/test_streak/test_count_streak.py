import datetime

from sqlalchemy.sql.expression import or_
from base import Session
from models.models import Habit, Record, Method, User
from unittest import TestCase
import unittest
from sqlalchemy import or_

"""
Test Situations for Count Method:

duration has more records than count
duration has equal records to count

"""


class TestCountStreakBase(TestCase):
    def setUp(self) -> None:
        self.user_id = 1
        self.today = datetime.date(2021, 12, 30)

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


class TestThreeDurationsOldestFullweekWeek(TestCountStreakBase):
    def setUp(self) -> None:
        self.user_id = 1
        self.today = datetime.date(2021, 12, 30)
        with Session(expire_on_commit=False) as s:
            user = User(self.user_id, 0)
            duration = "week"
            method = Method(type="count", duration=duration, count=4)
            s.add_all([user, method])
            s.commit()
            self.habit = Habit("count_habit_week_4days", user.id, method.id)
            s.add(self.habit)
            s.commit()
            self.records_oldest = [
                Record(user.id, self.habit.id, datetime.date(2021, 12, 13)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 16)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 18)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 19)),
            ]
            self.records_middle = [
                Record(user.id, self.habit.id, datetime.date(2021, 12, 21)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 22)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 24)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 25)),
            ]
            self.records_current = [
                Record(user.id, self.habit.id, datetime.date(2021, 12, 27)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 28)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 29)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 30)),
            ]

            s.bulk_save_objects(
                self.records_oldest + self.records_middle + self.records_current
            )
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
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 0)

    def test_oldest_half_middle_full_current_full(self):
        with Session() as s:
            s.query(Record).filter(
                Record.user == self.user_id,
                Record.date == self.records_oldest[2].date,
            ).delete()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 2)

    def test_oldest_half_middle_half_current_full(self):
        with Session() as s:
            s.query(Record).filter(
                Record.user == self.user_id,
                or_(
                    Record.date == self.records_oldest[2].date,
                    Record.date == self.records_middle[2].date,
                ),
            ).delete()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)

    def test_middle_half_oldest_full_current_full(self):
        with Session() as s:
            s.query(Record).filter(
                Record.user == self.user_id,
                Record.date == self.records_middle[2].date,
            ).delete()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)

    def test_middle_none_oldest_full_current_full(self):
        with Session() as s:
            s.query(Record).filter(
                Record.user == self.user_id,
                Record.date > self.records_oldest[-1].date,
                Record.date < self.records_current[0].date,
            ).delete()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)

    def test_middle_half_current_half_oldest_full(self):
        with Session() as s:
            s.query(Record).filter(
                Record.user == self.user_id,
                or_(
                    Record.date == self.records_current[2].date,
                    Record.date == self.records_middle[2].date,
                ),
            ).delete()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 0)

    def test_current_half_oldest_full_middle_full(self):
        with Session() as s:
            s.query(Record).filter(
                Record.user == self.user_id,
                Record.date == self.records_current[2].date,
            ).delete()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 2)

    def test_current_none_oldest_full_middle_full(self):
        with Session() as s:
            s.query(Record).filter(
                Record.user == self.user_id,
                Record.date > self.records_middle[-1].date,
            ).delete()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 2)

    def test_current_half_oldest_half_middle_full(self):
        with Session() as s:
            s.query(Record).filter(
                Record.user == self.user_id,
                or_(
                    Record.date == self.records_current[2].date,
                    Record.date == self.records_oldest[2].date,
                ),
            ).delete()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)


class TestOldestDurationLessDaysThanCountWeek(TestCountStreakBase):
    def setUp(self) -> None:

        self.user_id = 1
        self.today = datetime.date(2021, 12, 30)

        with Session(expire_on_commit=False) as s:

            user = User(self.user_id, 0)
            duration = "week"
            method = Method(type="count", duration=duration, count=4)
            s.add_all([user, method])
            s.commit()
            self.habit = Habit("count_habit_week_4days", user.id, method.id)
            s.add(self.habit)
            s.commit()
            self.record_oldest_1 = Record(
                user.id, self.habit.id, datetime.date(2021, 12, 24)
            )
            self.record_oldest_2 = Record(
                user.id, self.habit.id, datetime.date(2021, 12, 25)
            )
            self.record_oldest_3 = Record(
                user.id, self.habit.id, datetime.date(2021, 12, 26)
            )
            self.record_current_1 = Record(
                user.id, self.habit.id, datetime.date(2021, 12, 27)
            )
            records = [
                self.record_current_1,
                self.record_oldest_1,
                self.record_oldest_2,
                self.record_oldest_3,
            ]
            s.bulk_save_objects(records)
            s.commit()

    def test_oldest_all_full_current_half(self):
        with Session() as s:
            calculator = self.get_calculator()
            self.assertEqual(calculator.streak(), 1)

    def test_oldest_half_current_half(self):
        with Session() as s:
            s.query(Record).filter_by(
                user=self.user_id, date=self.record_oldest_2.date
            ).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 0)

    def test_oldest_none_full_current_half(self):
        with Session() as s:
            s.query(Record).filter(
                Record.user == self.user_id, Record.date < self.record_current_1.date
            ).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 0)

    def test_oldest_all_full_current_all_full(self):
        with Session() as s:

            self.record_current_2 = Record(
                self.user_id, self.habit.id, datetime.date(2021, 12, 28)
            )

            self.record_current_3 = Record(
                self.user_id, self.habit.id, datetime.date(2021, 12, 29)
            )

            self.record_current_4 = Record(
                self.user_id, self.habit.id, datetime.date(2021, 12, 30)
            )

            records = [
                self.record_current_2,
                self.record_current_3,
                self.record_current_4,
            ]
            s.bulk_save_objects(records)
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 2)

    def test_oldest_all_full_current_half(self):
        with Session() as s:
            self.record_current_2 = Record(
                self.user_id, self.habit.id, datetime.date(2021, 12, 28)
            )

            self.record_current_3 = Record(
                self.user_id, self.habit.id, datetime.date(2021, 12, 29)
            )

            records = [
                self.record_current_2,
                self.record_current_3,
            ]
            s.bulk_save_objects(records)
            s.commit()

        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)

    def test_oldest_all_full_current_none_full(self):
        with Session() as s:
            s.query(Record).filter(
                Record.user == self.user_id, Record.date > self.record_oldest_3.date
            ).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)


class TestOldestDurationEqualDaysToCountWeek(TestCountStreakBase):
    def setUp(self) -> None:

        self.user_id = 1
        self.today = datetime.date(2021, 12, 30)

        with Session(expire_on_commit=False) as s:

            user = User(self.user_id, 0)
            duration = "week"
            method = Method(type="count", duration=duration, count=4)
            s.add_all([user, method])
            s.commit()
            self.habit = Habit("count_habit_week_4days", user.id, method.id)
            s.add(self.habit)
            s.commit()
            self.record_oldest_1 = Record(
                user.id, self.habit.id, datetime.date(2021, 12, 23)
            )
            self.record_oldest_2 = Record(
                user.id, self.habit.id, datetime.date(2021, 12, 24)
            )
            self.record_oldest_3 = Record(
                user.id, self.habit.id, datetime.date(2021, 12, 25)
            )
            self.record_oldest_4 = Record(
                user.id, self.habit.id, datetime.date(2021, 12, 26)
            )
            self.record_current_1 = Record(
                user.id, self.habit.id, datetime.date(2021, 12, 27)
            )
            records = [
                self.record_current_1,
                self.record_oldest_1,
                self.record_oldest_2,
                self.record_oldest_3,
                self.record_oldest_4,
            ]
            s.bulk_save_objects(records)
            s.commit()

    def test_oldest_all_full_current_half(self):
        with Session() as s:
            calculator = self.get_calculator()
            self.assertEqual(calculator.streak(), 1)

    def test_oldest_half_current_half(self):
        with Session() as s:
            s.query(Record).filter_by(
                user=self.user_id, date=self.record_oldest_2.date
            ).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 0)

    def test_oldest_none_full_current_half(self):
        with Session() as s:
            s.query(Record).filter(
                Record.user == self.user_id, Record.date < self.record_current_1.date
            ).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 0)

    def test_oldest_all_full_current_all_full(self):
        with Session() as s:

            self.record_current_2 = Record(
                self.user_id, self.habit.id, datetime.date(2021, 12, 28)
            )

            self.record_current_3 = Record(
                self.user_id, self.habit.id, datetime.date(2021, 12, 29)
            )

            self.record_current_4 = Record(
                self.user_id, self.habit.id, datetime.date(2021, 12, 30)
            )

            records = [
                self.record_current_2,
                self.record_current_3,
                self.record_current_4,
            ]
            s.bulk_save_objects(records)
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 2)

    def test_oldest_all_full_current_half(self):
        with Session() as s:
            self.record_current_2 = Record(
                self.user_id, self.habit.id, datetime.date(2021, 12, 28)
            )

            self.record_current_3 = Record(
                self.user_id, self.habit.id, datetime.date(2021, 12, 29)
            )

            records = [
                self.record_current_2,
                self.record_current_3,
            ]
            s.bulk_save_objects(records)
            s.commit()

        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)

    def test_oldest_all_full_current_none_full(self):
        with Session() as s:
            s.query(Record).filter(
                Record.user == self.user_id, Record.date > self.record_oldest_4.date
            ).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)


class TestOldestDurationMoreDaysThanCountWeek(TestCountStreakBase):
    def setUp(self) -> None:

        self.user_id = 1
        self.today = datetime.date(2021, 12, 30)

        with Session(expire_on_commit=False) as s:

            user = User(self.user_id, 0)
            duration = "week"
            method = Method(type="count", duration=duration, count=4)
            s.add_all([user, method])
            s.commit()
            self.habit = Habit("count_habit_week_4days", user.id, method.id)
            s.add(self.habit)
            s.commit()
            self.record_oldest_1 = Record(
                user.id, self.habit.id, datetime.date(2021, 12, 22)
            )
            self.record_oldest_2 = Record(
                user.id, self.habit.id, datetime.date(2021, 12, 24)
            )
            self.record_oldest_3 = Record(
                user.id, self.habit.id, datetime.date(2021, 12, 25)
            )
            self.record_oldest_4 = Record(
                user.id, self.habit.id, datetime.date(2021, 12, 26)
            )
            self.record_current_1 = Record(
                user.id, self.habit.id, datetime.date(2021, 12, 27)
            )
            records = [
                self.record_current_1,
                self.record_oldest_1,
                self.record_oldest_2,
                self.record_oldest_3,
                self.record_oldest_4,
            ]
            s.bulk_save_objects(records)
            s.commit()

    def test_oldest_all_full_current_half(self):
        with Session() as s:
            calculator = self.get_calculator()
            self.assertEqual(calculator.streak(), 1)

    def test_oldest_half_current_half(self):
        with Session() as s:
            s.query(Record).filter_by(
                user=self.user_id, date=self.record_oldest_2.date
            ).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 0)

    def test_oldest_none_full_current_half(self):
        with Session() as s:
            s.query(Record).filter(
                Record.user == self.user_id, Record.date < self.record_current_1.date
            ).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 0)

    def test_oldest_all_full_current_all_full(self):
        with Session() as s:

            self.record_current_2 = Record(
                self.user_id, self.habit.id, datetime.date(2021, 12, 28)
            )

            self.record_current_3 = Record(
                self.user_id, self.habit.id, datetime.date(2021, 12, 29)
            )

            self.record_current_4 = Record(
                self.user_id, self.habit.id, datetime.date(2021, 12, 30)
            )

            records = [
                self.record_current_2,
                self.record_current_3,
                self.record_current_4,
            ]
            s.bulk_save_objects(records)
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 2)

    def test_oldest_all_full_current_half(self):
        with Session() as s:
            self.record_current_2 = Record(
                self.user_id, self.habit.id, datetime.date(2021, 12, 28)
            )

            self.record_current_3 = Record(
                self.user_id, self.habit.id, datetime.date(2021, 12, 29)
            )

            records = [
                self.record_current_2,
                self.record_current_3,
            ]
            s.bulk_save_objects(records)
            s.commit()

        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)

    def test_oldest_all_full_current_none_full(self):
        with Session() as s:
            s.query(Record).filter(
                Record.user == self.user_id, Record.date > self.record_oldest_4.date
            ).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)


class TestCurrentAndBeforeDurationsHaveNoRecords(TestCountStreakBase):
    def setUp(self) -> None:

        self.user_id = 1
        self.today = datetime.date(2021, 12, 30)

        with Session(expire_on_commit=False) as s:
            user = User(self.user_id, 0)
            duration = "week"
            method = Method(type="count", duration=duration, count=4)
            s.add_all([user, method])
            s.commit()
            self.habit = Habit("count_habit_week_4days", user.id, method.id)
            s.add(self.habit)
            s.commit()
            self.record_oldest_1 = Record(
                user.id, self.habit.id, datetime.date(2021, 12, 16)
            )
            self.record_oldest_2 = Record(
                user.id, self.habit.id, datetime.date(2021, 12, 17)
            )
            self.record_oldest_3 = Record(
                user.id, self.habit.id, datetime.date(2021, 12, 18)
            )
            self.record_oldest_4 = Record(
                user.id, self.habit.id, datetime.date(2021, 12, 19)
            )
            records = [
                self.record_oldest_1,
                self.record_oldest_2,
                self.record_oldest_3,
                self.record_oldest_4,
            ]
            s.bulk_save_objects(records)
            s.commit()

    def test_oldest_all_full(self):
        with Session() as s:
            calculator = self.get_calculator()
            self.assertEqual(calculator.streak(), 0)

    def test_oldest_half(self):
        with Session() as s:
            s.query(Record).filter_by(
                user=self.user_id, date=self.record_oldest_2.date
            ).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 0)


class OldestDurationisCurrentDuration(TestCountStreakBase):
    def setUp(self) -> None:
        self.user_id = 1
        self.today = datetime.date(2021, 12, 30)

        with Session(expire_on_commit=False) as s:
            user = User(self.user_id, 0)
            duration = "week"
            method = Method(type="count", duration=duration, count=4)
            s.add_all([user, method])
            s.commit()
            self.habit = Habit("count_habit_week_4days", user.id, method.id)
            s.add(self.habit)
            s.commit()
            self.record_1 = Record(user.id, self.habit.id, datetime.date(2021, 12, 27))
            self.record_2 = Record(user.id, self.habit.id, datetime.date(2021, 12, 28))
            self.record_3 = Record(user.id, self.habit.id, datetime.date(2021, 12, 29))
            self.record_4 = Record(user.id, self.habit.id, datetime.date(2021, 12, 30))
            records = [
                self.record_1,
                self.record_2,
                self.record_3,
                self.record_4,
            ]
            s.bulk_save_objects(records)
            s.commit()

    def test_duration_all_full(self):
        with Session() as s:
            calculator = self.get_calculator()
            self.assertEqual(calculator.streak(), 1)

    def test_duration_half(self):
        with Session() as s:
            s.query(Record).filter_by(
                user=self.user_id, date=self.record_2.date
            ).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 0)

    def test_duration_none_full(self):
        with Session() as s:
            s.query(Record).filter_by(user=self.user_id).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 0)


if __name__ == "__main__":
    unittest.main()
