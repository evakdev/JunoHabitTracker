from base import Session
from models import User
from models import Habit, Record

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

def create_user(telegram_id):
    with Session() as s:
        user = s.query(User).filter_by(telegram_id=telegram_id).one_or_none()
        if not user:
            user = User(telegram_id=telegram_id)
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

