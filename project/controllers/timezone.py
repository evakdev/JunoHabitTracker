from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.ext.filters import Filters
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.messagehandler import MessageHandler
from controllers.crud import create_user, get_user
from controllers.base import Conversation
from controllers.mainkeys import timezone, edit_timezone
from controllers.ptbshortcuts import get_from_user, send_message


class Timezone(Conversation):
    def __init__(self):
        super().__init__()
        self.entry_points = [
            CallbackQueryHandler(self.ask_timezone, pattern=f"^{self.keys.id}$"),
            CallbackQueryHandler(self.edit_timezone, pattern=f"^{self.keys.edit}$"),
            CommandHandler(edit_timezone, self.edit_timezone),
        ]
        self.states = {
            self.keys.answer1: [
                MessageHandler(Filters.regex("[/]+"), callback=self.filter_error),
                # 👆 so that commands are not taken as timezone.Not allowing the user
                # to go back to main here, because they have to set a timezone first and be saved in database..
                MessageHandler(Filters.text, self.get_timezone),
            ]
        }
        self.name = "Timezone Setter"
        self.create_handler()

    def add_keys(self):
        super().add_keys()
        self.keys.id = timezone
        self.keys.edit = edit_timezone
        self.keys.answer1 = self.keys.id + "1"

    def edit_timezone(self, update, context):
        user = get_user(get_from_user(update).id)
        if not user:
            return self.ask_timezone(update, context)
        text = (
            f"Your current timezone is {self.readable_timezone(user.timezone)}.\n"
            "Send me your new timezone offset to change it.\n"
            "\n"
            "💡 Tip: Use <a href='https://time.is/time_zones'>this website</a> to find yours."
        )
        send_message(update, text, parse_mode="HTML")
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
        return self.save(update, context)

    def save(self, update, context):
        user = create_user(id=update.message.from_user.id, timezone=self.timezone)
        return self.back_to_main(update, context)

    def back_to_main(self, update, context):
        text = (
            f"⏰ Your timezone is {self.readable_timezone(self.timezone)}.\n"
            "You're all set! Click to go back to main menu."
        )
        keyboard = InlineKeyboardMarkup([self.main_menu_button])
        update.message.reply_text(text, reply_markup=keyboard)
        return self.keys.main_menu

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
        text = (
            "the timezone format is wrong. Please send it in the correct format.\n"
            "\n"
            "<b>Accepted Formats:</b>\n"
            "<code>1, -1, 1.5, 1.45\n"
            "1:00, -1:00, 1:30, 1:45\n"
            "utc 1, gmt 1</code>"
        )
        update.message.reply_text(text=text, parse_mode="HTML")
        return self.keys.answer1

    def filter_error(self, update, context):
        text = (
            "Sorry, you can't use / here, that's reserved for bot commands.\n"
            "please send your time zone again.\n"
            "You have to set a timezone to be able to use the bot."
        )
        update.message.reply_text(text)
        return self.keys.answer1
