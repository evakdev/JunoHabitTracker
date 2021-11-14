from base import Session
from models.models import User, Habit, Record
from models.models import Method

def create_habit(name,user,**kwargs):
    with Session() as s:
        habit = s.query(Habit).filter_by(name=name,user=user).one_or_none()
        if habit:
            return None
        habit = Habit(name=name,user=user)
        if kwargs.get('method_id'):
            habit.method_id=kwargs.get('method_id')
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
        return user

def create_record(user,habit,date):
    with Session() as s:
        record = s.query(Record).filter_by(user=user,habit=habit,date=date).one_or_none()
        if not record:
            record = Record(user=user,habit=habit,date=date)
            s.add(record)
            s.commit()
        return record

def create_method(*args, **kwargs):
    """required kwargs: type, duration
    optional kwargs: specified, interval, count
    you should have exactly one of the optional kwargs."""
    
    type_ = kwargs.pop('type')
    duration = kwargs.pop('duration')
    if not(type_ and duration):
        return None
        
    with Session() as s:
        method = Method(type_, duration, **kwargs)
        s.add(method)
        s.commit()
        return method

def add_method(habit,method):
    with Session() as s:
        habit = s.merge(habit)
        method = s.merge(method)
        habit.method = method.id
        s.commit()
        return habit
        
def get_user(id):
    """gets user from db by their telegram id."""
    with Session() as s:
        user = s.query(User).filter_by(id=id).one_or_none()
        return user

def get_habit(name, user_id):
    """gets habit from db by users id and habits name"""
    with Session() as s:
        habit = s.query(Habit).filter_by(name=name,user=user_id).one_or_none()
        return habit