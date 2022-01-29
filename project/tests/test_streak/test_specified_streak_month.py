import datetime
import unittest
from sqlalchemy.sql.expression import or_
from base import Session
from models.models import Habit, Record, Method, User
from unittest import TestCase


class TestSpecifiedStreakBase(TestCase):
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


class TestNoRecordsExist(TestSpecifiedStreakBase):
    def setUp(self) -> None:
        self.user_id = 1
        self.today = datetime.date(2021, 12, 25)
        with Session(expire_on_commit=False) as s:
            user = User(self.user_id, 0)
            duration = "month"
            method = Method(
                type="specified", duration=duration, specified=[5, 10, 15]
            )  # fifth, tenth, and fifteenth days of the month
            s.add_all([user, method])
            s.commit()
            self.habit = Habit("specified_habit_month_051015", user.id, method.id)
            s.add(self.habit)
            s.commit()

    def test_no_records_exist(self):
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 0)


class TestThreeDurationsOldestFullmonth(TestSpecifiedStreakBase):
    def setUp(self) -> None:
        self.user_id = 1
        self.today = datetime.date(2021, 12, 25)
        with Session(expire_on_commit=False) as s:
            user = User(self.user_id, 0)
            duration = "month"
            method = Method(
                type="specified", duration=duration, specified=[5, 10, 15]
            )  # fifth, tenth, and fifteenth days of the month
            s.add_all([user, method])
            s.commit()
            self.habit = Habit("specified_habit_month_051015", user.id, method.id)
            s.add(self.habit)
            s.commit()

            self.records_oldest = [
                Record(user.id, self.habit.id, datetime.date(2021, 10, 5)),
                Record(user.id, self.habit.id, datetime.date(2021, 10, 10)),
                Record(user.id, self.habit.id, datetime.date(2021, 10, 15)),
            ]
            self.records_middle = [
                Record(user.id, self.habit.id, datetime.date(2021, 11, 5)),
                Record(user.id, self.habit.id, datetime.date(2021, 11, 10)),
                Record(user.id, self.habit.id, datetime.date(2021, 11, 15)),
            ]
            self.records_current = [
                Record(user.id, self.habit.id, datetime.date(2021, 12, 5)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 10)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 15)),
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
            record = Record(self.user_id, self.habit.id, datetime.date(2021, 10, 23))
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
            record = Record(self.user_id, self.habit.id, datetime.date(2021, 12, 23))
            s.add(record)
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 3)


class OldestDurationIsCurrentDuration(TestSpecifiedStreakBase):
    def setUp(self) -> None:
        self.user_id = 1
        self.today = datetime.date(2021, 12, 25)
        with Session(expire_on_commit=False) as s:
            user = User(self.user_id, 0)
            duration = "month"
            method = Method(
                type="specified", duration=duration, specified=[5, 10, 25]
            )  # fifth, tenth, and twenty fifth days of the month
            s.add_all([user, method])
            s.commit()
            self.habit = Habit("specified_habit_month_051025", user.id, method.id)
            s.add(self.habit)
            s.commit()

            self.records = [
                Record(user.id, self.habit.id, datetime.date(2021, 12, 5)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 10)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 25)),
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


class TestOldestStartsInMiddleofmonth(TestSpecifiedStreakBase):
    def setUp(self) -> None:
        self.user_id = 1
        self.today = datetime.date(2021, 12, 25)
        with Session(expire_on_commit=False) as s:
            user = User(self.user_id, 0)
            duration = "month"
            method = Method(
                type="specified", duration=duration, specified=[5, 10, 15]
            )  # fifth, tenth, and fifteenth days of the month
            s.add_all([user, method])
            s.commit()
            self.habit = Habit("specified_habit_month_051015", user.id, method.id)
            s.add(self.habit)
            s.commit()

            self.records_oldest = [
                Record(user.id, self.habit.id, datetime.date(2021, 11, 10)),
                Record(user.id, self.habit.id, datetime.date(2021, 11, 15)),
            ]
            self.records_current = [
                Record(user.id, self.habit.id, datetime.date(2021, 12, 5)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 10)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 15)),
            ]
            s.bulk_save_objects(self.records_oldest + self.records_current)
            s.commit()

    def test_oldest_available_specified_are_full_current_full_oldest_full(self):
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 2)

    def test_oldest_has_logs_outside_specified_oldest_full_current_full(self):
        with Session() as s:
            record = Record(self.user_id, self.habit.id, datetime.date(2021, 11, 7))
            s.add(record)
            s.commit()

        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 2)

    def test_oldest_has_logs_outside_specified_oldest_half_current_full(self):
        with Session() as s:
            record = Record(self.user_id, self.habit.id, datetime.date(2021, 11, 7))
            s.query(Record).filter_by(
                user=self.user_id, date=self.records_oldest[-1].date
            ).delete()
            s.add(record)
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)

    def test_oldest_has_logs_outside_specified_equal_to_available_specified_oldest_none_current_full(
        self,
    ):
        with Session() as s:

            s.query(Record).filter(
                Record.user == self.user_id, Record.date < self.records_current[0].date
            ).delete()
            s.commit()
            record = Record(self.user_id, self.habit.id, datetime.date(2021, 11, 23))
            s.add(record)
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)

    def test_oldest_has_logs_outside_specified_less_than_available_specified_oldest_none_current_full(
        self,
    ):
        with Session() as s:

            s.query(Record).filter(
                Record.user == self.user_id, Record.date < self.records_current[0].date
            ).delete()
            s.commit()
            record = Record(self.user_id, self.habit.id, datetime.date(2021, 11, 14))
            s.add(record)
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)


class TestCurrentEndsMiddleofMonth(TestSpecifiedStreakBase):
    def setUp(self) -> None:
        self.user_id = 1
        self.today = datetime.date(2021, 12, 12)
        with Session(expire_on_commit=False) as s:
            user = User(self.user_id, 0)
            duration = "month"
            method = Method(
                type="specified", duration=duration, specified=[5, 10, 15]
            )  # fifth, tenth, and fifteenth days of the month
            s.add_all([user, method])
            s.commit()
            self.habit = Habit("specified_habit_month_051015", user.id, method.id)
            s.add(self.habit)
            s.commit()

            self.records_oldest = [
                Record(user.id, self.habit.id, datetime.date(2021, 11, 5)),
                Record(user.id, self.habit.id, datetime.date(2021, 11, 10)),
                Record(user.id, self.habit.id, datetime.date(2021, 11, 15)),
            ]
            self.records_current = [
                Record(user.id, self.habit.id, datetime.date(2021, 12, 5)),
                Record(user.id, self.habit.id, datetime.date(2021, 12, 10)),
            ]
            s.bulk_save_objects(self.records_current + self.records_oldest)
            s.commit()

    def test_current_available_specified_are_full_current_half_oldest_full(self):
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)

    def test_current_has_logs_outside_specified_equal_to_missing_specified_current_half_oldest_full(
        self,
    ):
        with Session() as s:
            record = Record(self.user_id, self.habit.id, datetime.date(2021, 12, 7))
            s.add(record)
            s.commit()

        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)

    def test_current_has_logs_outside_specified_less_than_missing_specified_current_half_oldest_full(
        self,
    ):
        with Session() as s:
            record = Record(self.user_id, self.habit.id, datetime.date(2021, 12, 3))
            s.add(record)
            s.query(Record).filter_by(
                user=self.user_id, date=self.records_current[-1].date
            ).delete()
            s.commit()
        self.today = datetime.date(2021, 12, 7)
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)

    def test_current_has_logs_outside_specified_oldest_full_current_none(self):
        with Session() as s:
            s.query(Record).filter(
                Record.user == self.user_id, Record.date > self.records_oldest[-1].date
            ).delete()
            s.commit()
            records = [
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 7)),
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 14)),
            ]
            s.add_all(records)
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)


class TestNoSpecifiedDaysInCurrentOrOldestDuration(TestSpecifiedStreakBase):
    def setUp(self) -> None:
        self.user_id = 1
        self.today = datetime.date(2021, 12, 4)
        with Session(expire_on_commit=False) as s:
            user = User(self.user_id, 0)
            duration = "month"
            method = Method(
                type="specified", duration=duration, specified=[5, 10, 15]
            )  # fifth, tenth, fifteenth day of the month
            s.add_all([user, method])
            s.commit()
            self.habit = Habit("specified_habit_month_051015", user.id, method.id)
            s.add(self.habit)
            s.commit()
            self.method_id = method.id

            self.records_oldest = [
                Record(user.id, self.habit.id, datetime.date(2021, 11, 25)),
            ]
            self.records_current = [
                Record(user.id, self.habit.id, datetime.date(2021, 12, 3)),
            ]
            s.bulk_save_objects(self.records_current, self.records_oldest)
            s.commit()

    def test_no_specified_days_in_either_oldest_none_current_none(self):
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 0)

    def test_no_specified_days_in_oldest_current_full(self):
        self.today = datetime.date(2021, 12, 25)
        with Session() as s:
            records = [
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 5)),
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 10)),
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 15)),
            ]
            s.add_all(records)
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)

    def test_no_specified_days_in_current_oldest_full(self):
        with Session() as s:
            records = [
                Record(self.user_id, self.habit.id, datetime.date(2021, 11, 5)),
                Record(self.user_id, self.habit.id, datetime.date(2021, 11, 10)),
                Record(self.user_id, self.habit.id, datetime.date(2021, 11, 15)),
            ]
            s.add_all(records)
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 1)

    def test_one_specified_available_in_oldest_is_full_current_full(self):
        self.today = datetime.date(2021, 12, 25)
        with Session() as s:
            records = [
                Record(
                    self.user_id, self.habit.id, datetime.date(2021, 11, 15)
                ),  # oldest
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 5)),
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 10)),
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 15)),
            ]
            s.add_all(records)
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 2)

    def test_one_specified_available_in_current_is_full_oldest_full(self):
        self.today = datetime.date(2021, 12, 6)
        with Session() as s:
            records = [
                Record(self.user_id, self.habit.id, datetime.date(2021, 11, 5)),
                Record(self.user_id, self.habit.id, datetime.date(2021, 11, 10)),
                Record(self.user_id, self.habit.id, datetime.date(2021, 11, 15)),
                Record(
                    self.user_id, self.habit.id, datetime.date(2021, 12, 5)
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
            records = [
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 2)),
                # 3 already exists
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 4)),
            ]
            s.add_all(records)
            s.commit()
        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 0)

    def test_no_specified_days_in_either_but_oldest_has_other_logs_equal_to_len_of_specified(
        self,
    ):
        with Session() as s:
            records = [
                # 25 already exists
                Record(self.user_id, self.habit.id, datetime.date(2021, 11, 26)),
                Record(self.user_id, self.habit.id, datetime.date(2021, 11, 27)),
            ]
            s.add_all(records)
            s.commit()

        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 0)

    def test_no_specified_days_in_either_but_both_have_other_logs_equal_to_len_of_specified(
        self,
    ):
        with Session() as s:
            current = [
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 2)),
                # 3 already exists
                Record(self.user_id, self.habit.id, datetime.date(2021, 12, 4)),
            ]
            oldest = [
                # 25 already exists
                Record(self.user_id, self.habit.id, datetime.date(2021, 11, 26)),
                Record(self.user_id, self.habit.id, datetime.date(2021, 11, 27)),
            ]
            s.add_all(current + oldest)
            s.commit()

        calculator = self.get_calculator()
        self.assertEqual(calculator.streak(), 0)


if __name__ == "__main__":
    unittest.main()
