from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from controllers.base import Conversation
from controllers.methods import Everyday, Interval, Count, Specified

everyday = Everyday()
interval = Interval()
count = Count()
specified = Specified()


class MethodCreator(Conversation):
    def __init__(self):
        super().__init__()

        self.entry_points = [CallbackQueryHandler(self.ask_type, pattern=self.keys.id)]
        self.states = {
            self.keys.answer1: [
                everyday.handler,
                interval.handler,
                count.handler,
                specified.handler,
            ],
        }

        self.name = "Method Creator"
        self.create_handler()

    def add_keys(self):
        super().add_keys()
        self.keys.id = "methodcreator"
        self.keys.answer1 = self.keys.id + "1"

    def create_handler(self):
        super().create_handler()
        # This is overwritten because methods are fourth-level conversations,
        # and need to return end, not self.keys.main_menu, so that main menu
        # menu buttons work if user presses /main.
        self.handler._map_to_parent = {
            self.keys.goback: self.keys.methodend,
            self.keys.end: self.keys.end,
        }

    def ask_type(self, update, context):
        buttons = [
            [InlineKeyboardButton("Every day", callback_data=everyday.keys.id)],
            [InlineKeyboardButton("Every X days", callback_data=interval.keys.id)],
            [InlineKeyboardButton("X days a week/month", callback_data=count.keys.id)],
            [
                InlineKeyboardButton(
                    "Specific days of the week/month", callback_data=specified.keys.id
                )
            ],
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        text = "how often do you want to do this habit?"
        update.callback_query.edit_message_text(text, reply_markup=keyboard)
        return self.keys.answer1
