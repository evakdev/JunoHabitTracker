from telegram import replymarkup
from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.ext.filters import Filters
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.conversationhandler import ConversationHandler
from telegram.ext.messagehandler import MessageHandler
from controllers.crud import create_user, add_timezone, get_user
from controllers.base import Conversation


class Timezone(Conversation):
    def __init__(self):
        super().__init__()
        self.handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.ask_timezone, pattern=f"^{self.keys.id}$"),
                CallbackQueryHandler(self.edit_timezone, pattern=f"^{self.keys.edit}$"),
            ],
            states={
                self.keys.answer1: [MessageHandler(Filters.text, self.get_timezone)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            map_to_parent={self.keys.end: self.keys.goback},
            name="Timezone Setter",
        )

    def add_keys(self):
        super().add_keys()
        self.keys.id = "timezone"
        self.keys.edit = self.keys.id + "edit"
        self.keys.answer1 = self.keys.id + "1"

    def edit_timezone(self, update, context):
        user = get_user(update.callback_query.from_user.id)
        if not user:
            return
        text = (
            f"Your current timezone is {self.readable_timezone(user.timezone)}.\n"
            "Send me your new timezone offset to change it.\n"
            "\n"
            "Tip: Use https://time.is/time_zones to find yours."
        )
        update.callback_query.edit_message_text(text=text)
        return self.keys.answer1

    def ask_timezone(self, update, context):

        text = (
            "Please send me you UTC timezone offset. It should be something similar to this: UTC +1\n"
            "\n"
            "You can find yours on https://time.is/time_zones. Just copy the title of the section where your country is, and send it to me!"
        )
        update.callback_query.edit_message_text(text=text)
        return self.keys.answer1

    def get_timezone(self, update, context):
        self.timezone = self.clean_timezone(update.message.text, update, context)
        if not -12 <= self.timezone <= 12:
            return self.wrong_timezone(update, context)
        user = create_user(id=update.message.from_user.id, timezone=self.timezone)
        if not user.timezone:
            add_timezone(user, self.timezone)
        return self.back_to_main(update, context)

    def back_to_main(self, update, context):
        text = (
            f"⏰ Your timezone is {self.readable_timezone(self.timezone)}.\n"
            "You're all set! Click to go back to main menu."
        )
        button = [InlineKeyboardButton("↪ Main Menu", callback_data=self.keys.goback)]
        keyboard = InlineKeyboardMarkup([button])
        update.message.reply_text(text, reply_markup=keyboard)
        return self.keys.end

    def clean_timezone(self, timezone, update, context):
        to_remove = {
            "utc": "",
            "gmt": "",
            " ": "",
            "/": "",
            ":30": ".5",
            ":45": ".75",
        }
        timezone = timezone.lower()
        for key, value in to_remove.items():
            timezone = timezone.replace(key, value)

        try:
            timezone = float(timezone)
            return timezone
        except:
            return self.wrong_timezone(update, context)

    def readable_timezone(self, timezone):
        if timezone == 0:
            return "UTC 0"

        a, b = str(timezone).split(".")
        to_replace = {"5": ":30", "75": ":45", "0": "", "00": ""}
        for key, value in to_replace.items():
            if b == key:
                b = value

        readable = a + b
        if timezone > 0:
            readable = "+" + readable
        return "UTC " + readable

    def wrong_timezone(self, update, context):
        text = "the timezone format is wrong. Please send it in the correct format."
        update.message.reply_text(text=text)
        return self.keys.answer1
