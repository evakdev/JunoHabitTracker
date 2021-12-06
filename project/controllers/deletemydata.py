from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.ext.conversationhandler import ConversationHandler
from telegram.ext.commandhandler import CommandHandler
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from controllers.crud import get_user, delete_habit, delete_user
from controllers.base import Conversation
from controllers.mixins import MainMenuMixin


class DeleteMyData(MainMenuMixin, Conversation):
    def __init__(self):
        super().__init__()
        self.handler = ConversationHandler(
            entry_points=[
                CommandHandler("deleteall", self.give_warning),
                CallbackQueryHandler(self.give_warning, pattern=self.keys.id),
            ],
            states={
                self.keys.answer1: [
                    CallbackQueryHandler(
                        self.delete_everything, pattern=self.keys.confirmed
                    ),
                    CallbackQueryHandler(self.main_menu, pattern=self.keys.main_menu),
                ],
            },
            fallbacks=[CommandHandler(self.keys.cancel, self.cancel)],
            map_to_parent={self.keys.end: self.keys.main_menu},
            name="Delete My Data",
        )

    def add_keys(self):
        super().add_keys()
        self.keys.id = "deletemydata"
        self.keys.answer1 = self.keys.id + "1"
        self.keys.confirmed = self.keys.id + "confirmed"

    def main_menu(self, update, context):
        super().main_menu(update, context)
        return self.keys.end

    def give_warning(self, update, context):
        text = (
            "This will remove ALL of your data from the bot. It will be as if you were never here.\n"
            "All of your info, habits, records will all be erased.\n"
            "\n"
            "<b>🔺 Are you sure you want to do this?</b>\n"
            "\n"
            "Tip: If you want to remove only a single habit, go to 'Manage Habits' menu."
        )
        buttons = [
            [
                InlineKeyboardButton(
                    "Yes, delete it all.", callback_data=self.keys.confirmed
                )
            ],
            self.main_menu_button,
        ]
        keyboard = InlineKeyboardMarkup(buttons)

        update.callback_query.edit_message_text(
            text, reply_markup=keyboard, parse_mode="HTML"
        )
        return self.keys.answer1

    def delete_everything(self, update, context):
        user = get_user(update.callback_query.from_user.id)
        user_habits = user.get_habits()
        for habit in user_habits:
            delete_habit(habit, delete_records=True, delete_method=True)
        delete_user(user.id)
        return self.say_goodbye(update, context)

    def say_goodbye(self, update, context):
        text = (
            "All of your data has been deleted.\n"
            "If you ever want to come back, just click on /start.\n"
            "\n"
            "Bye! 👋"
        )
        update.callback_query.edit_message_text(text)
        return self.keys.end
