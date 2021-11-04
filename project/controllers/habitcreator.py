from telegram.ext.filters import Filters
from telegram.replykeyboardmarkup import ReplyKeyboardMarkup
from base import dispatcher
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.conversationhandler import ConversationHandler
from telegram.ext.messagehandler import MessageHandler
from controllers.crud import create_habit

NEWHABIT, HABITMAKER, METHODMAKER, DONE = range(4)

def new_habit(update, context):
    update.message.reply_text("What should we name your new habit?")
    return HABITMAKER

def habit_maker(update, context):
    user_id = update.message.from_user.id
    habit_name = "".join(update.message.text).capitalize()
    habit = create_habit(habit_name, user_id)

    if habit:
        update.message.reply_text(
            f"Awesome! How do you want to track {update.message.text}?"
        )
        return METHODMAKER
    else:
        update.message.reply_text(
            "Looks like you already have that habit!",
            "go to /managehabits to edit it if you want, or enter a new name.",
        )
        return HABITMAKER


def method_maker(update, context):
    user_id = update.message.from_user.id
    # new_habit =
    reply_markup = ReplyKeyboardMarkup(
        [["👍", "👎"]],
        one_time_keyboard=True,
    )
    update.message.reply_text(
        "All right, assigned this method for you.",
        "click on 👍 to finish up!",
        reply_markup=reply_markup,
    )
    return DONE


def done(update, context):
    update.message.reply_text(
        "All done!",
        "Anytime you want, you can go to /managehabit to edit your habits,",
        "or go to /newhabit to create new ones!",
    )
    return ConversationHandler.END


def cancel(update, context) -> int:
    user = update.message.from_user
    update.message.reply_text("cancelling command.")

    return ConversationHandler.END


convo_handler = ConversationHandler(
    entry_points=[CommandHandler("newhabit", new_habit)],
    states={
        HABITMAKER: [MessageHandler(Filters.text, habit_maker)],
        METHODMAKER: [MessageHandler(Filters.text, method_maker)],
        DONE: [MessageHandler(Filters.regex("^(👍|👎)$"), done)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)


dispatcher.add_handler(convo_handler)
