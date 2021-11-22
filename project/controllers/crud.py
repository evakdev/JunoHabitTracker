from base import Session
from models.models import User, Habit, Record
from models.models import Method


def create_habit(name, user, **kwargs):
    with Session() as s:
        habit = s.query(Habit).filter_by(name=name, user=user).one_or_none()
        if habit:
            return None
        habit = Habit(name=name, user=user)
        if kwargs.get("method_id"):
            habit.method_id = kwargs.get("method_id")
        s.add(habit)
        s.commit()
        return habit


def create_user(id, timezone):
    with Session() as s:
        user = s.query(User).filter_by(id=id).one_or_none()
        if not user:
            user = User(id=id, timezone=timezone)
            s.add(user)
            s.commit()

        s.refresh(user)
        return user


def create_record(user_id, habit_id, date):
    with Session() as s:
        record = (
            s.query(Record).filter_by(user=user_id, habit=habit_id, date=date).one_or_none()
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

    with Session() as s:
        method = Method(type_, duration, **kwargs)
        s.add(method)
        s.commit()
        return method


def add_method(habit, method):
    with Session() as s:
        habit = s.merge(habit)
        method = s.merge(method)
        habit.method = method.id
        s.commit()
        return habit


def add_timezone(user, timezone):
    with Session() as s:

        s.merge(user)
        user.timezone = timezone
        s.commit()


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

def find_habit_by_name(habit_name, user_id):
    """Gets habit from db by user id and habit name. 
    Returns none if user has no habit in that name.
    """
    with Session() as s:
        habit = s.query(Habit).filter_by(name=habit_name, user=user_id).one_or_none()
        return habit
def edit_habit(habit, *args, **kwargs):
    """Works with either habit or its id.
    will edit name, and/or method.
    to edit method, provide new method's id or object."""
    with Session() as s:
        if type(habit)==int:
            habit = s.query(Habit).filter_by(id=id).one_or_none()
        name = kwargs.get('name')
        method = kwargs.get('method')
        if name:
            habit.name=name
        if method:
            method=method.id if type(method)==Method else method
            old_method_id=habit.method
            habit.method = method
            old_method=s.query(Method).filter_by(id=old_method_id).one_or_none()
            old_method.delete()
        s.commit()
        s.refresh(habit)
        


            
            
        
    
    name = kwargs.get('name')
    method = kwargs.get('method')
    
        

    
def get_method(id):
    with Session() as s:
        method = s.query(Method).filter_by(id=id).one_or_none()
        return method

def get_record(user_id, habit_id, date):
    with Session() as s:
        record = (
            s.query(Record).filter_by(user=user_id, habit=habit_id, date=date).one_or_none()
        )
        return record

def delete_record(record):
    with Session() as s:
        s.delete(record)
        s.commit()