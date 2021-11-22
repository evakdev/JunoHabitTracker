
from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.ext.conversationhandler import ConversationHandler
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.filters import Filters
from telegram.ext.messagehandler import MessageHandler

from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from controllers.crud import create_method
from controllers.base import Conversation
from controllers.methods import Everyday,Interval,Count,Specified

everyday = Everyday()
interval = Interval()
count = Count()
specified = Specified()

class MethodCreator(Conversation):
    def __init__(self):
        super().__init__()
        types = [everyday.handler,interval.handler,count.handler,specified.handler]

        self.handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.ask_type, pattern=self.keys.id)],
            states={
                self.keys.answer1: types,
            },
            fallbacks=[CommandHandler(self.keys.cancel, self.cancel)],
            map_to_parent={self.keys.backtomain: self.keys.methodend,},
            name='Method Creator'
        )
     
    def add_keys(self):
        super().add_keys()
        self.keys.id = "methodcreator"
        self.keys.answer1 = self.keys.id + "1"
        self.keys.methodend = 'methodend'

    def ask_type(self, update,context):
        buttons = [
                [InlineKeyboardButton("Every day", callback_data=everyday.keys.id)],
                [InlineKeyboardButton("Every X days", callback_data=interval.keys.id)],
                [InlineKeyboardButton("X days a week/month", callback_data=count.keys.id)],
                [InlineKeyboardButton("Specific days of the week/month", callback_data=specified.keys.id)],
            ]
        keyboard = InlineKeyboardMarkup(buttons)
        text = "how often do you want to do this habit?"
        update.callback_query.edit_message_text(text, reply_markup=keyboard)
        return self.keys.answer1
    
