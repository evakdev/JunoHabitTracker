from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.ext.filters import Filters
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.conversationhandler import ConversationHandler
from telegram.ext.messagehandler import MessageHandler
from controllers.crud import create_habit, add_method
from controllers.methodcreator import MethodCreator
from controllers.base import Conversation

methodcreator = MethodCreator()


class HabitCreator(Conversation):
    def __init__(self):
        super().__init__()
        self.handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.ask_name, pattern=f"^{self.keys.id}$")
            ],
            states={
                self.keys.answer1: [
                    MessageHandler(Filters.text, callback=self.get_name)
                ],
                self.keys.answer2: [methodcreator.handler],
                self.keys.goback: [
                    CallbackQueryHandler(self.end, pattern=f"^{self.keys.goback}$")
                ],
            },
            fallbacks=[CommandHandler(self.keys.cancel, self.cancel)],
            map_to_parent={self.keys.end: self.keys.goback},
            name="Habit Creator",
        )

    def add_keys(self):
        super().add_keys()
        self.keys.id = "habitcreator"
        self.keys.methodend = methodcreator.keys.methodend
        self.keys.answer1 = self.keys.id + "1"
        self.keys.answer2 = self.keys.id + "2"

    def ask_name(self, update, context):
        update.callback_query.edit_message_text("What should we name your new habit?")
        return self.keys.answer1

    def get_name(self, update, context):
        user_id = update.message.from_user.id
        self.habit_name = "".join(
            update.message.text
        ).capitalize()  # will need habit name later.
        self.habit = create_habit(self.habit_name, user_id)
        if self.habit:
            return self.ask_method(update, context)

        text = (
            "Looks like you already have that habit!\n"
            "go to /managehabits to edit it if you want, or enter a new name."
        )
        update.message.reply_text(text)
        return self.keys.answer1

    def ask_method(self, update, context):

        text = "Awesome. Now let's see how you want to track this habit..."
        button = InlineKeyboardButton("Go on", callback_data=methodcreator.keys.id)
        keyboard = InlineKeyboardMarkup([[button]])
        update.message.reply_text(text, reply_markup=keyboard)
        return self.keys.answer2

    def end(self, update, context):
        method = context.user_data.get("method")
        add_method(self.habit, method)

        text = (
            "All done!\n"
            f"Starting from now, you can start logging for {self.habit_name}.\n"
            "\n"
            "Now go get it done! 💪"
        )
        button = InlineKeyboardButton(
            "↩ Back to Main Menu", callback_data=self.keys.goback
        )
        keyboard = InlineKeyboardMarkup([[button]])

        update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
        return self.keys.end
