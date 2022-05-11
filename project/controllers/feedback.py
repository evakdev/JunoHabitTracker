from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.filters import Filters
from telegram.ext.messagehandler import MessageHandler
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from process.env import feedback_channel_id
from controllers.base import Conversation
from controllers.ptbshortcuts import send_message, get_from_user
from controllers import mainkeys

import textwrap


class Feedback(Conversation):
    def __init__(self):
        super().__init__()
        self.feedback_text = ""
        self.finish_keyword = "done"
        self.char_limit = 4096

        self.entry_points = [
            CommandHandler(self.keys.id, self.ask_feedback),
            CallbackQueryHandler(self.ask_feedback, pattern=f"^{self.keys.id}$"),
        ]
        self.states = {
            self.keys.answer1: [MessageHandler(Filters.text, self.get_feedback)],
        }
        self.name = "Feedback"
        self.create_handler()

    def add_keys(self):
        super().add_keys()
        self.keys.id = mainkeys.feedback
        self.keys.answer1 = "answer1"

    def ask_feedback(self, update, context):
        self.feedback_text = (
            f"<b>Feedback from <code>{get_from_user(update).id}</code></b>\n\n"
        )

        text = (
            "I'm all ears! 👂\n"
            "Feel free to send as many messages as you want.\n"
            "\n"
            f"When you're done, send <code>{self.finish_keyword}</code> to let me know you finished."
        )

        send_message(update, text, parse_mode="HTML")
        return self.keys.answer1

    def get_feedback(self, update, context):
        message = update.message.text
        if message.lower().strip() == self.finish_keyword:
            return self.send_feedback(update, context)
        self.feedback_text += message + "\n"
        return self.keys.answer1

    def send_feedback(self, update, context):
        if len(self.feedback_text) > self.char_limit:
            messages = self.split_feedback_message()
        else:
            messages = [self.feedback_text]

        for message in messages:
            context.bot.send_message(
                chat_id=feedback_channel_id, text=message, parse_mode="HTML"
            )
        return self.say_thanks(update, context)

    def say_thanks(self, update, context):
        text = "Thanks a lot for your feedback! 💌\n"
        keyboard = InlineKeyboardMarkup([self.main_menu_button])
        send_message(update, text, reply_markup=keyboard)
        return self.keys.main_menu

    def split_feedback_message(self):
        feedback_message_list = []
        remaining_text = self.feedback_text
        while len(remaining_text) >= self.char_limit:
            message = textwrap.shorten(
                remaining_text, width=self.char_limit, break_long_words=True
            )
            feedback_message_list.append(message)
            starting_index = len(message) - 3
            if remaining_text[starting_index] == " ":
                starting_index += 1
            remaining_text = remaining_text[starting_index:]
        feedback_message_list.append(remaining_text)
        return feedback_message_list
