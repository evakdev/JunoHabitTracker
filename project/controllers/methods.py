from telegram.ext.commandhandler import CommandHandler
from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.ext.messagehandler import MessageHandler
from telegram.ext.filters import Filters
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from controllers.crud import create_method
from controllers.base import Conversation
from controllers.ptbshortcuts import send_message


# Base Class
class MethodConversation(Conversation):
    def __init__(self):
        super().__init__()

    def add_keys(self):
        super().add_keys()

    def create_handler(self):
        super().create_handler()
        # This is overwritten because methods are fourth-level conversations,
        # and need to return end, not self.keys.main_menu, so that main menu
        # menu buttons work if user presses /main..
        self.handler._map_to_parent = {
            self.keys.goback: self.keys.goback,
            self.keys.end: self.keys.end,
        }

    def end(self, update, context):

        text = "Okay, let's save all this..."
        button = [InlineKeyboardButton("Save", callback_data=self.keys.methodend)]
        keyboard = InlineKeyboardMarkup([button])

        try:
            update.message.reply_text(text, reply_markup=keyboard)
        except:
            update.callback_query.edit_message_text(text, reply_markup=keyboard)

        return self.keys.goback

    def add_to_dict(self, update, context):
        pass


# Methods
class Everyday(MethodConversation):
    def __init__(self):
        super().__init__()
        self.entry_points = [
            CallbackQueryHandler(self.add_to_dict, pattern=f"^{self.keys.id}$")
        ]
        self.states = {str: []}
        self.name = "Everyday Method"
        self.create_handler()

    def add_keys(self):
        super().add_keys()
        self.keys.id = "everyday"

    def add_to_dict(self, update, context):
        method_dict = {
            "type": "interval",
            "duration": "day",
            "interval": 1,
        }
        context.user_data["method"] = method_dict
        return self.end(update, context)


class Interval(MethodConversation):
    def __init__(self):
        super().__init__()
        self.entry_points = [
            CallbackQueryHandler(self.add_to_dict, pattern=f"^{self.keys.id}$")
        ]
        self.states = {
            self.keys.answer1: [
                MessageHandler(
                    filters=Filters.regex(pattern=r"^[1-9]*$"),
                    callback=self.get_interval,
                )
            ]
        }
        self.name = "Interval Method"
        self.create_handler()

    def add_keys(self):
        super().add_keys()
        self.keys.id = "interval"
        self.keys.answer1 = self.keys.id + "1"

    def add_to_dict(self, update, context):
        method_dict = {
            "type": self.keys.id,
            "duration": "day",
        }
        context.user_data["method"] = method_dict
        return self.ask_interval(update, context)

    def ask_interval(self, update, context):
        text = (
            "Fill in the blank:\n"
            "I want to do this every ... days.\n"
            "\n"
            "<b>Example:</b>\n"
            "1 means every day\n"
            "2 means every other day; e.g. Saturday, Monday, Wednesday, ..."
        )
        update.callback_query.edit_message_text(text, parse_mode="HTML")
        return self.keys.answer1

    def get_interval(self, update, context):
        # should have a pattern of numbers.
        days = int(update.message.text)
        context.user_data["method"]["interval"] = days
        return self.end(update, context)


class Count(MethodConversation):
    def __init__(self):
        super().__init__()
        self.entry_points = [
            CallbackQueryHandler(self.add_to_dict, pattern=f"^{self.keys.id}$")
        ]
        self.states = {
            self.keys.answer1: [
                CallbackQueryHandler(
                    self.get_duration,
                    pattern=f"^{self.keys.week}$|^{self.keys.month}$",
                )
            ],
            self.keys.answer2: [
                MessageHandler(
                    filters=Filters.regex(pattern=r"^[0-9]*$"),
                    callback=self.get_count,
                )
            ],
        }

        self.name = "Count Method"
        self.create_handler()

    def add_keys(self):
        super().add_keys()
        self.keys.id = "count"
        self.keys.week = "week"
        self.keys.month = "month"
        self.keys.answer1 = self.keys.id + "1"
        self.keys.answer2 = self.keys.id + "2"

    def add_to_dict(self, update, context):
        method_dict = {
            "type": self.keys.id,
        }
        context.user_data["method"] = method_dict
        return self.ask_duration(update, context)

    def ask_duration(self, update, context):
        text = "Do you want to track based on the week, or the month?"
        buttons = [
            [
                InlineKeyboardButton("Week", callback_data=self.keys.week),
                InlineKeyboardButton("Month", callback_data=self.keys.month),
            ]
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        update.callback_query.edit_message_text(text, reply_markup=keyboard)
        return self.keys.answer1

    def get_duration(self, update, context):
        self.duration = update.callback_query.data
        if not self.duration in [self.keys.week, self.keys.month]:
            return self.keys.cancel
        context.user_data.get("method")["duration"] = self.duration
        return self.ask_count(update, context)

    def ask_count(self, update, context):
        text = f"How many times a {self.duration} do you want to do this habit?"
        update.callback_query.edit_message_text(text)
        return self.keys.answer2

    def get_count(self, update, context):
        count = update.message.text
        if self.count_is_valid(count):
            context.user_data.get("method")["count"] = int(count)
            return self.end(update, context)
        return self.wrong_count(update, context)

    def wrong_count(self, update, context):
        text = f"Please enter a valid number between 1 and {7 if self.duration==self.keys.week else 28}."
        if self.count_is_over_28:
            text += "\nI can't track monthly for more than 28 days, because it will mess up your streak at odd months. Maybe you could use the <em>everyday</em> method instead?"

        update.message.reply_text(text)
        return self.keys.answer2

    def count_is_valid(self, count):
        self.count_is_over_28 = False
        if count == "" or count == "0":
            return False
        try:
            count = int(count)
        except:
            return False

        if self.duration == self.keys.week:
            return count <= 7
        if self.duration == self.keys.month:
            if count > 28:
                self.count_is_over_28 = True
                return count <= 28
            # 28 to avoid butchering streaks in odd months with 29,30,31 days.


class Specified(MethodConversation):
    def __init__(self):
        super().__init__()
        self.buttons = list()
        self.entry_points = [
            CallbackQueryHandler(self.add_to_dict, pattern=f"^{self.keys.id}$")
        ]
        self.states = {
            self.keys.answer1: [
                CallbackQueryHandler(
                    self.get_duration,
                    pattern=f"^{self.keys.week}$|^{self.keys.month}$",
                )
            ],
            self.keys.answer2: [
                CallbackQueryHandler(self.get_specified, pattern="^day[0-9]+$")
            ],
        }
        self.name = "Specified Method"

        self.create_handler()

    def add_keys(self):
        super().add_keys()
        self.keys.id = "specified"
        self.keys.week = "week"
        self.keys.month = "month"
        self.keys.done = "day0"
        self.keys.answer1 = self.keys.id + "1"
        self.keys.answer2 = self.keys.id + "2"

    def add_to_dict(self, update, context):
        method_dict = {
            "type": self.keys.id,
        }
        context.user_data["method"] = method_dict
        return self.ask_duration(update, context)

    def ask_duration(self, update, context):
        text = "Do you want to track based on the week, or the month?"
        buttons = [
            [
                InlineKeyboardButton("Week", callback_data=self.keys.week),
                InlineKeyboardButton("Month", callback_data=self.keys.month),
            ]
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        update.callback_query.edit_message_text(text, reply_markup=keyboard)
        return self.keys.answer1

    def get_duration(self, update, context):
        self.duration = update.callback_query.data
        if not self.duration in [self.keys.week, self.keys.month]:
            return self.keys.end
        context.user_data.get("method")["duration"] = self.duration
        return self.ask_specified(update, context)

    def ask_specified(self, update, context):

        text = f"Which days of the {self.duration} do you want to do this habit?"
        self.create_buttons()
        keyboard = InlineKeyboardMarkup(self.buttons)
        update.callback_query.edit_message_text(text, reply_markup=keyboard)
        return self.keys.answer2

    def get_specified(self, update, context):

        if update.callback_query.data == self.keys.done:
            return self.pressed_done(update, context)
        choice = update.callback_query.data
        context.user_data.get("method")["specified"] = self.update_days(context, choice)
        self.update_buttons(choice)
        text = f"You can choose as many days as you want. when you're done, click Done."
        keyboard = InlineKeyboardMarkup(self.buttons)
        update.callback_query.edit_message_text(text, reply_markup=keyboard)
        return self.keys.answer2

    def pressed_done(self, update, context):
        if context.user_data.get("method").get("specified"):

            return self.end(update, context)
        text = "❌ You must choose at least one day."
        keyboard = InlineKeyboardMarkup(self.buttons)
        update.callback_query.edit_message_text(text, reply_markup=keyboard)
        return self.keys.answer2

    def create_buttons(self):
        done_button = InlineKeyboardButton("Done", callback_data=self.keys.done)
        if self.duration == self.keys.week:
            self.buttons = [
                [InlineKeyboardButton("Monday", callback_data="day1")],
                [InlineKeyboardButton("Tuesday", callback_data="day2")],
                [InlineKeyboardButton("Wednesday", callback_data="day3")],
                [InlineKeyboardButton("Thursday", callback_data="day4")],
                [InlineKeyboardButton("Friday", callback_data="day5")],
                [InlineKeyboardButton("Saturday", callback_data="day6")],
                [InlineKeyboardButton("Sunday", callback_data="day7")],
                [done_button],
            ]
        elif self.duration == self.keys.month:
            self.buttons = [
                [
                    InlineKeyboardButton(str(i + j), callback_data=f"day{i+j}")
                    for j in range(1, 6)
                ]
                for i in range(0, 26, 5)
            ]
            self.buttons[-1] = self.buttons[-1][:3]
            self.buttons.append([done_button])

    def is_checked(self, button):
        return button.text.startswith("✅")

    def update_buttons(self, choice):
        for i, row in enumerate(self.buttons):
            for j, button in enumerate(row):
                if button.callback_data != choice:
                    continue
                if self.is_checked(button):
                    text = button.text.replace("✅", "")
                else:
                    text = button.text = "✅ " + button.text
                self.buttons[i][j] = InlineKeyboardButton(
                    text, callback_data=button.callback_data
                )
                return
        return

    def update_days(self, context, choice):
        days = context.user_data.get("method").get("specified", list())
        clean_choice = int(choice.replace("day", ""))
        if clean_choice in days:
            days.remove(clean_choice)
        else:
            days.append(clean_choice)
        return days
