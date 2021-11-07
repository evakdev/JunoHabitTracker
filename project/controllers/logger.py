from telegram.ext.filters import Filters
from telegram.replykeyboardmarkup import ReplyKeyboardMarkup
from base import dispatcher
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.conversationhandler import ConversationHandler
from telegram.ext.messagehandler import MessageHandler
from controllers.crud import get_user
from controllers.helpers import get_3_days_for_timezone
from controllers.crud import create_record, get_habit
from controllers.helpers import make_days_readable

SELECTHABIT, SELECTDAY = range(2)


def log(update, context):
    user = get_user(update.message.from_user.id)
    context.user_data['object'] = user
    reply_markup = ReplyKeyboardMarkup(
        [user.habits],
        one_time_keyboard=True,
        resize_keyboard=True
    )

    update.message.reply_text(
        "Which habit are you logging for?", reply_markup=reply_markup
    )
    return SELECTHABIT


def select_habit(update, context):
    user = context.user_data.get('object')
    habit = get_habit(update.message.text, user.id)
    days = make_days_readable(get_3_days_for_timezone(user.timezone))
    context.user_data['habit']=habit
    context.user_data['days']=days
    reply_markup = ReplyKeyboardMarkup(
        [days.keys()],
        one_time_keyboard=True,resize_keyboard=True
    )
    update.message.reply_text(
        "Which day are you logging for?", reply_markup=reply_markup
    )
    return SELECTDAY

def select_day(update,context):
    user = context.user_data.get('object')
    habit = context.user_data.get('habit')
    date = context.user_data.get('days').get(update.message.text)
    create_record(user.id,habit.id,date)
    update.message.reply_text(
        f"""Logged for {habit.name} on {date.strftime("%A %B %d")}. 
        Well done! 🎉""")
    return ConversationHandler.END


def cancel(update, context) -> int:
    user = update.message.from_user
    update.message.reply_text("cancelling command.")
    return ConversationHandler.END


convo_handler = ConversationHandler(
    entry_points=[CommandHandler("log", log)],
    states={SELECTHABIT: [MessageHandler(Filters.text, select_habit)],
    SELECTDAY: [MessageHandler(Filters.text, select_day)]},
    fallbacks=[CommandHandler("cancel", cancel)],
)

dispatcher.add_handler(convo_handler)
