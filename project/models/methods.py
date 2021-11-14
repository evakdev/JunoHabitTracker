from abc import ABC
from models import MethodBase
from datetime import timedelta, date

from project.base import Session
from project.models.models import Record
from math import ceil

ALLMETHODS = []

# Durations
week = "week"
month = "month"
year = "year"


class MethodCalculator(ABC):
    def __init__(self, records, *args, **kwargs):
        self._streak = 0
        self.today = date.today()
        self.records = records
        self.first_date_ever = records.last().date
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
    def __init__(self, records, interval, duration):
        self.interval = interval
        self.duration = duration
        super().__init__(records)

    def streak(self):
        records = self.records.all()
        last_date = records[0].date
        if len(records) == 0 or self.streak_is_broken(last_date):
            return 0
        for record in records:
            if record.date - last_date <= timedelta(days=self.interval-1):
                self._streak += 1
                last_date = record.date
            else:
                break
        return self._streak

    def streak_is_broken(self, last_date):
        if self.today - last_date > timedelta(days=self.interval-1):
            return True


class CountCalculator(MethodCalculator):
    def __init__(self, records, count, duration):
        self.count = count
        self.duration = duration
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


class SpecificCalculator(MethodCalculator):
    def __init__(self, records, days, duration):
        self.days = days.sort(reverse=True)
        self.duration = duration
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


