import datetime

from sqlalchemy.sql.expression import or_
from base import Session
from models.models import Habit, Record, Method, User
from unittest import TestCase
import unittest


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
                specified=method.specified_days,
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


class TestThreeDurationsOldestFullweek(TestCountStreakBase):
    def setUp(self) -> None:
        self.user_id = 1
        self.today = datetime.date(2021, 12, 31)
        with Session(expire_on_commit=False) as s:
            user = User(self.user_id, 0)
            duration = "week"
            method = Method(
                type="specified", duration=duration, specified=[1, 3, 5]
            )  # Mon, Wed, Fri
            s.add_all([user, method])
            s.commit()
            self.habit = Habit("specified_habit_week_135", user.id, method.id)
            s.add(self.habit)
            s.commit()

            self.records_oldest = [
                Record(user.id, self.habit.id, datetime.date(2021, 12, 13)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 15)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 17)),
            ]
            self.records_middle = [
                Record(user.id, self.habit.id, datetime.date(2021, 12, 20)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 22)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 24)),
            ]
            self.records_current = [
                Record(user.id, self.habit.id, datetime.date(2021, 12, 27)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 29)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 31)),
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
                    Record.date == self.records_oldest[1].date,
                    Record.date == self.records_middle[1].date,
                    Record.date == self.records_current[1].date,
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
            record = Record(self.user_id, self.habit.id, datetime.date(2021, 12, 14))
            s.add(record)
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 3)

    def test_middle_more_than_count_oldest_full_current_full(self):
        with Session() as s:
            record = Record(self.user_id, self.habit.id, datetime.date(2021, 12, 23))
            s.add(record)
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 3)

    def test_current_more_than_count_oldest_full_middle_full(self):
        with Session() as s:
            record = Record(self.user_id, self.habit.id, datetime.date(2021, 12, 28))
            s.add(record)
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 3)


class OldestDurationIsCurrentDuration(TestCountStreakBase):
    def setUp(self) -> None:
        self.user_id = 1
        self.today = datetime.date(2021, 12, 31)
        with Session(expire_on_commit=False) as s:
            user = User(self.user_id, 0)
            duration = "week"
            method = Method(
                type="specified", duration=duration, specified=[1, 3, 5]
            )  # Mon, Wed, Fri
            s.add_all([user, method])
            s.commit()
            self.habit = Habit("specified_habit_week_135", user.id, method.id)
            s.add(self.habit)
            s.commit()

            self.records = [
                Record(user.id, self.habit.id, datetime.date(2021, 12, 27)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 29)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 31)),
            ]

            s.bulk_save_objects(self.records)
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
            s.query(Record).filter_by(user=self.user_id, date=self.records[1]).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 0)

    def test_duration_none(self):
        with Session() as s:
            s.query(Record).filter_by(user=self.user_id).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 0)


class TestOldestStartsInMiddleofWeek(TestCountStreakBase):
    def setUp(self) -> None:
        self.user_id = 1
        self.today = datetime.date(2021, 12, 31)
        with Session(expire_on_commit=False) as s:
            user = User(self.user_id, 0)
            duration = "week"
            method = Method(
                type="specified", duration=duration, specified=[1, 3, 5]
            )  # Mon, Wed, Fri
            s.add_all([user, method])
            s.commit()
            self.habit = Habit("specified_habit_week_135", user.id, method.id)
            s.add(self.habit)
            s.commit()

            self.records_oldest = [
                Record(user.id, self.habit.id, datetime.date(2021, 12, 22)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 24)),
            ]
            self.records_current = [
                Record(user.id, self.habit.id, datetime.date(2021, 12, 27)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 29)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 31)),
            ]
            s.bulk_save_objects(self.records_current)
            s.commit()

    def test_oldest_available_specified_are_full_current_full_oldest_full(self):
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 2)

    def test_oldest_has_logs_outside_specified_oldest_full_current_full(self):
        with Session() as s:
            record = Record(self.user_id, self.habit.id, datetime.date(2021, 12, 23))
            s.add(record)
            s.commit()

        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 2)

    def test_oldest_has_logs_outside_specified_oldest_half_current_full(self):
        with Session() as s:
            record = Record(self.user_id, self.habit.id, datetime.date(2021, 12, 23))
            s.query(Record).filter_by(
                user=self.user_id, date=self.records_oldest[-1]
            ).delete()
            s.add(record)
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)

    def test_oldest_has_logs_outside_specified_equal_to_available_specified_oldest_none_current_full(
        self,
    ):
        with Session() as s:

            s.query(Record).filter_by(user=self.user_id).delete()
            s.commit()
            record = Record(self.user_id, self.habit.id, datetime.date(2021, 12, 23))
            s.add(record)
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)

    def test_oldest_has_logs_outside_specified_less_than_available_specified_oldest_none_current_full(
        self,
    ):
        with Session() as s:

            s.query(Record).filter_by(user=self.user_id).delete()
            s.commit()
            record = Record(self.user_id, self.habit.id, datetime.date(2021, 12, 21))
            s.add(record)
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)


class TestCurrentEndsMiddleofWeek(TestCountStreakBase):
    def setUp(self) -> None:
        self.user_id = 1
        self.today = datetime.date(2021, 12, 30)
        with Session(expire_on_commit=False) as s:
            user = User(self.user_id, 0)
            duration = "week"
            method = Method(
                type="specified", duration=duration, specified=[1, 3, 5]
            )  # Mon, Wed, Fri
            s.add_all([user, method])
            s.commit()
            self.habit = Habit("specified_habit_week_135", user.id, method.id)
            s.add(self.habit)
            s.commit()

            self.records_oldest = [
                Record(user.id, self.habit.id, datetime.date(2021, 12, 20)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 22)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 24)),
            ]
            self.records_current = [
                Record(user.id, self.habit.id, datetime.date(2021, 12, 27)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 29)),
            ]
            s.bulk_save_objects(self.records_current, self.records_oldest)
            s.commit()

    def test_current_available_specified_are_full_current_half_oldest_full(self):
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)

    def test_current_has_logs_outside_specified_equal_to_missing_specified_current_half_oldest_full(
        self,
    ):
        with Session() as s:
            record = Record(self.user_id, self.habit.id, datetime.date(2021, 12, 28))
            s.add(record)

            s.commit()

        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)

    def test_current_has_logs_outside_specified_less_than_missing_specified_current_half_oldest_full(
        self,
    ):
        with Session() as s:
            record = Record(self.user_id, self.habit.id, datetime.date(2021, 12, 28))
            s.add(record)
            s.query(Record).filter_by(
                user=self.user_id, date=self.records_current[-1].date
            ).delete()
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)

    def test_current_has_logs_outside_specified_oldest_full_current_none(self):
        with Session() as s:
            s.query(Record).filter_by(user=self.user_id).delete()
            s.commit()
            records = [
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 28)),
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 30)),
            ]
            s.add_all(records)
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)


class TestNoSpecifiedDaysInCurrentOrOldestDuration(TestCountStreakBase):
    def setUp(self) -> None:
        self.user_id = 1
        self.today = datetime.date(2021, 12, 28)
        with Session(expire_on_commit=False) as s:
            user = User(self.user_id, 0)
            duration = "week"
            method = Method(
                type="specified", duration=duration, specified=[3, 4, 5]
            )  # Mon, Wed, Fri
            s.add_all([user, method])
            s.commit()
            self.habit = Habit("specified_habit_week_345", user.id, method.id)
            s.add(self.habit)
            s.commit()
            self.method_id = method.id

            self.records_oldest = [
                Record(user.id, self.habit.id, datetime.date(2021, 12, 25)),
            ]
            self.records_current = [
                Record(user.id, self.habit.id, datetime.date(2021, 12, 27)),
            ]
            s.bulk_save_objects(self.records_current, self.records_oldest)
            s.commit()

    def test_no_specified_days_in_oldest_current_full(self):
        self.today = datetime.date(2021, 12, 31)
        with Session() as s:
            records = [
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 29)),
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 30)),
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 31)),
            ]
            s.add_all(records)
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)

    def test_no_specified_days_in_current_oldest_full(self):
        with Session() as s:
            records = [
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 22)),
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 23)),
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 24)),
            ]
            s.add_all(records)
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)

    def test_one_specified_available_in_oldest_is_full_current_full(self):
        self.today = datetime.date(2021, 12, 31)
        with Session() as s:
            records = [
                Record(
                    self.user_id, self.habit.id, datetime.date(2021, 12, 24)
                ),  # oldest
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 29)),
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 30)),
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 31)),
            ]
            s.add_all(records)
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 2)

    def test_one_specified_available_in_current_is_full_oldest_full(self):
        self.today = datetime.date(2021, 12, 29)
        with Session() as s:
            records = [
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 22)),
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 23)),
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 24)),
                Record(
                    self.user_id, self.habit.id, datetime.date(2021, 12, 29)
                ),  # current
            ]
            s.add_all(records)
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)

    def test_no_specified_days_in_either_but_current_has_other_logs_equal_to_len_of_specified(
        self,
    ):
        with Session() as s:
            method = s.query(Method).filter_by(id=self.method_id).one()
            method.specified = method.convert_specified([3, 4])
            record = Record(self.user_id, self.habit.id, datetime.date(2021, 12, 28))
            s.add(record)
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 0)

    def test_no_specified_days_in_either_but_oldest_has_other_logs_equal_to_len_of_specified(
        self,
    ):
        with Session() as s:
            method = s.query(Method).filter_by(id=self.method_id).one()
            method.specified = method.convert_specified([3, 4])
            record = Record(self.user_id, self.habit.id, datetime.date(2021, 12, 26))
            s.add(record)
            s.commit()

        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 0)

    def test_no_specified_days_in_either_but_both_have_other_logs_equal_to_len_of_specified(
        self,
    ):
        with Session() as s:
            method = s.query(Method).filter_by(id=self.method_id).one()
            method.specified = method.convert_specified([3, 4])
            records = [
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 26)),
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 28)),
            ]
            s.add(records)
            s.commit()

        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 0)

