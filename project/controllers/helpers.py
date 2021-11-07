from datetime import datetime, timedelta
from telegram.ext import CommandHandler
from base import dispatcher
from pytz import utc


def add_handler(command, func):
    handler = CommandHandler(command, func)
    dispatcher.add_handler(handler)


def get_3_days_for_timezone(timezone):
    "returns today, yesterday, and the day before for the timezone"
    today = (datetime.now(tz=utc) + timedelta(hours=timezone)).date()
    return [(today + timedelta(days=i)) for i in range(3)]

def make_days_readable(days):
    "returns a dictionary of date options and date objects"
    daydict = {
        f"Today ({days[0].strftime('%A')})":days[0],
        f"Yesterday ({days[1].strftime('%A')})":days[1],
        f"{days[2].strftime('%A')}":days[2],
    }
    return daydict
