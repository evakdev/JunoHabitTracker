from base import dispatcher
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.conversationhandler import ConversationHandler
import re
from telegram.ext.filters import Filters
from telegram.ext.messagehandler import MessageHandler
from telegram.replykeyboardmarkup import ReplyKeyboardMarkup

from controllers.crud import create_user

TZMESSAGE, TIMEZONE = range(2)
start_msg = "Awesome, lets start!"
cancel_msg = "nah, cancel"


def start(update, context):
    user_name = update.message.from_user.first_name
    message = f"""
    Hi there {user_name}! 
    I'm Juno, your personal habit tracker! 
    You can add as many habits as you want, decide how often you want to do them, and keep up your streak!
    Ready to start adding some habits?
    

    """
    reply_markup = ReplyKeyboardMarkup(
        [[start_msg, cancel_msg]], one_time_keyboard=True, resize_keyboard=True
    )
    update.message.reply_text(message, reply_markup=reply_markup)
    return TZMESSAGE


def tzmessage(update, context):

    message = """In order to show you dates correctly, I need to know your timezone offset. It should be something similar to this: UTC +1
    If you dont know yours, go to https://time.is/time_zones and find the section with your country name in the page. 
    Then just copy the title of that section for me and you're done!

    Note: if you dont feel comfortable sharing your timezone, you can always use UTC +0. Just note that your dates might be shown wrongly.
    """
    update.message.reply_text(message)
    return TIMEZONE


def timezone(update, context):
    try:
        timezone = float(re.sub(r"u|t|c|U|T|C| ", "", update.message.text))
        if not -12 <= timezone <= 12:
            raise ValueError
        create_user(id=update.message.from_user.id, timezone=timezone)
        message = "You're all done! use /newhabit to create your first habit"
        update.message.reply_text(message)
        return ConversationHandler.END

    except Exception as e:
        print(e)
        update.message.reply_text(
            "The timezone format is wrong. please send it in the correct format."
        )
        return TIMEZONE


def cancel(update, context) -> int:
    user = update.message.from_user
    update.message.reply_text("cancelling command.")

    return ConversationHandler.END


convo_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        TZMESSAGE: [MessageHandler(Filters.regex(f"{start_msg}"), tzmessage)],
        TIMEZONE: [MessageHandler(Filters.text, timezone)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
dispatcher.add_handler(convo_handler)