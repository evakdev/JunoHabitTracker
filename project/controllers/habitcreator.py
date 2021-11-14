from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.ext.filters import Filters
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
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
        context.user_data['habit'] = dict()
        context.user_data['habit']['object'] = habit
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('Next', callback_data='next')]])
        update.message.reply_text(
            "Awesome. Click on next to go to the next step.",
            reply_markup=keyboard,
        )
        """
        update.message.reply_text(
            f"Awesome! How do you want to track {update.message.text}?"
        )"""
        return METHODMAKER
    else:
        update.message.reply_text(
            "Looks like you already have that habit!"
            "go to /managehabits to edit it if you want, or enter a new name."
        )
        return HABITMAKER



from controllers.crud import add_method
def done(update, context):
    info = context.user_data.get('habit')
    add_method(info['object'], info['method'])

    update.callback_query.edit_message_text(
        "All done!"
        "Starting from now, you can start logging using /log."
        "Now go get it done! 💪"
    )
    return ConversationHandler.END


def cancel(update, context) -> int:
    user = update.message.from_user
    update.message.reply_text("cancelling command.")

    return ConversationHandler.END

from controllers.methodmaker import method_convo_handler, METHODCHOICEEND

convo_handler = ConversationHandler(
    entry_points=[CommandHandler("newhabit", new_habit)],
    states={
        HABITMAKER: [MessageHandler(Filters.text, habit_maker)],
        METHODMAKER: [method_convo_handler],
        METHODCHOICEEND: [CallbackQueryHandler(callback=done, pattern=f'^save$')],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    name ='convo handler'
)


dispatcher.add_handler(convo_handler)
