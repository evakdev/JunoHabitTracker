from base import Session
from models.models import User, Habit, Record, Method


##### Create #####


def create_habit(name, user, method):
    with Session(expire_on_commit=False) as s:
        if type(method) == Method:
            s.merge(method)
            method = method.id
        if type(user) == User:
            s.merge(user)
            user = user.id

        habit = s.query(Habit).filter_by(name=name, user=user).one_or_none()
        if habit:
            return None
        habit = Habit(name=name, user=user, method=method)
        s.add(habit)
        s.commit()
        return habit


def create_user(id, timezone):
    with Session(expire_on_commit=False) as s:
        user = s.query(User).filter_by(id=id).one_or_none()
        if not user:
            user = User(id=id, timezone=timezone)
            s.add(user)
            s.commit()

        return user


def create_record(user_id, habit_id, date):
    with Session(expire_on_commit=False) as s:
        record = (
            s.query(Record)
            .filter_by(user=user_id, habit=habit_id, date=date)
            .one_or_none()
        )
        if record:
            return None
        record = Record(user=user_id, habit=habit_id, date=date)
        s.add(record)
        s.commit()
        return record


def create_method(*args, **kwargs):
    """required kwargs: type, duration
    optional kwargs: specified, interval, count
    you should have exactly one of the optional kwargs."""

    type_ = kwargs.pop("type")
    duration = kwargs.pop("duration")
    if not (type_ and duration):
        return None

    with Session(expire_on_commit=False) as s:
        method = Method(type_, duration, **kwargs)
        s.add(method)
        s.commit()
        return method


##### Get #####


def get_user(id):
    """gets user from db by their telegram id."""
    with Session() as s:
        user = s.query(User).filter_by(id=id).one_or_none()
        return user


def get_habit(id, user_id):
    """gets habit from db by users id and habit id"""
    with Session() as s:
        habit = s.query(Habit).filter_by(id=id, user=user_id).one_or_none()
        return habit


def get_habit_by_name(habit_name, user_id):
    """Gets habit from db by user id and habit name.
    Returns none if user has no habit in that name.
    """
    with Session() as s:
        habit = s.query(Habit).filter_by(name=habit_name, user=user_id).one_or_none()
        return habit


def get_method(id):
    with Session() as s:
        method = s.query(Method).filter_by(id=id).one_or_none()
        return method


def get_record(user_id, habit_id, date):
    with Session() as s:
        record = (
            s.query(Record)
            .filter_by(user=user_id, habit=habit_id, date=date)
            .one_or_none()
        )
        return record


##### Edit #####


def edit_habit(habit, new_name=None, new_method=None):
    """Works with either habit or its id.
    will edit name, and/or method.
    to edit method, provide new method's id or object."""
    with Session() as s:
        if type(habit) != int:
            s.merge(habit)
            habit = habit.id

        if new_name:
            s.query(Habit).filter_by(id=habit).update({"name": new_name})
        if new_method:
            old_method_id = s.query(Habit).filter_by(id=habit).one().method
            new_method = new_method.id if type(new_method) == Method else new_method
            s.query(Habit).filter_by(id=habit).update({"method": new_method})
            s.query(Method).filter_by(id=old_method_id).delete()

        s.commit()


##### Delete #####


def delete_record(record):
    with Session() as s:
        s.delete(record)
        s.commit()


def delete_habit(habit, delete_records=True, delete_method=True):
    with Session() as s:
        if delete_records:
            records = s.query(Record).filter_by(habit=habit.id)
            records.delete(synchronize_session=False) if records.count() else None

        method_id = habit.method
        habit = s.query(Habit).filter_by(id=habit.id).one_or_none()
        s.delete(habit)

        if delete_method:
            method = s.query(Method).filter_by(id=method_id)
            method.delete(synchronize_session=False) if method.count() else None
        s.commit()


def delete_user(user_id):
    with Session() as s:
        user = s.query(User).filter_by(id=user_id)
        user.delete(synchronize_session=False) if user.count() else None
        s.commit()
