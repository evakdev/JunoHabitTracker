from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.ext.commandhandler import CommandHandler
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from datetime import datetime, timedelta
from pytz import utc
from controllers import crud
from controllers.base import Conversation
from controllers.mixins import ChooseHabitMixin
from controllers.mainkeys import log


class Logger(ChooseHabitMixin, Conversation):
    def __init__(self):
        super().__init__()
        self.name = "Logger"
        self.entry_points = [
            CommandHandler(log, self.ask_habit),
            CallbackQueryHandler(self.ask_habit, pattern=self.keys.id),
        ]

        self.states = self.choose_habit_states | {
            self.keys.answer1: [
                CallbackQueryHandler(self.get_date, pattern="^[0-9]+-[0-9]+-[0-9]+$"),
                CallbackQueryHandler(
                    self.log_exists,
                    pattern=f"^{self.keys.log_exists}[0-9]+-[0-9]+-[0-9]+$",
                ),
                CallbackQueryHandler(self.ask_task, pattern=f"^{self.keys.done}$"),
            ],
            self.keys.answer3: [
                CallbackQueryHandler(
                    self.remove_log, pattern=f"^[0-9]+-[0-9]+-[0-9]+$"
                ),
                CallbackQueryHandler(self.ask_date, pattern=self.keys.answer1),
            ],
            self.keys.answer4: [
                self.main_menu_callback_state,
                CallbackQueryHandler(self.ask_date, pattern="^[0-9]+:[0-9]+$"),
                CallbackQueryHandler(self.ask_habit, pattern=self.keys.id),
                CallbackQueryHandler(
                    self.get_streak, pattern=f"^{self.keys.streak}:[0-9]+$"
                ),
            ],
        }

        self.create_handler()

        self.user = None
        self.habit = None
        self.date = None

    def add_keys(self):
        super().add_keys()
        self.keys.id = log
        self.keys.answer1 = self.keys.id + "1"
        self.keys.answer3 = self.keys.id + "3"
        self.keys.answer4 = self.keys.id + "4"
        self.keys.streak = "streak"
        self.keys.log_exists = self.keys.id + "exists"
        self.keys.done = self.keys.id + "done"

    def ask_habit(self, update, context):
        if self.user_doesnt_exist(update):
            return self.redirect_to_timezone(update, context)
        self.choose_habit_text = "Which habit are you logging for?"
        return super().ask_habit(update, context)

    def get_habit(self, update, context):
        update_, context_ = super().get_habit(update, context)
        return self.ask_date(update_, context_)

    def ask_date(self, update, context):
        self.find_three_days(self.user.timezone)
        self.create_date_buttons()
        keyboard = InlineKeyboardMarkup(self.date_buttons)
        text = (
            f"Logging for {self.habit.name}\n"
            "Select a day to mark it as done!\n"
            "\n"
            "💡 <b>Tip</b>: If a day has ✅, you've already logged for that day.\n"
        )
        update.callback_query.edit_message_text(
            text, reply_markup=keyboard, parse_mode="HTML"
        )
        return self.keys.answer1

    def get_date(self, update, context):
        self.date = datetime.strptime(update.callback_query.data, "%Y-%m-%d").date()
        record = crud.create_record(self.user.id, self.habit.id, self.date)
        return self.ask_date(update, context)

    def log_exists(self, update, context):
        text = "You've already logged for that day! Do you want to delete your log?"
        date = update.callback_query.data.replace(self.keys.log_exists, "")

        buttons = [
            [InlineKeyboardButton("❌ Yes, delete it.", callback_data=date)],
            [InlineKeyboardButton("↩ No, go back", callback_data=self.keys.answer1)],
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        update.callback_query.edit_message_text(text, reply_markup=keyboard)
        return self.keys.answer3

    def remove_log(self, update, context):
        self.date = datetime.strptime(update.callback_query.data, "%Y-%m-%d").date()
        record = crud.get_record(self.user.id, self.habit.id, self.date)
        crud.delete_record(record)
        return self.ask_date(update, context)

    def ask_task(self, update, context):
        text = "Well done! 💪\n" "What else can I do for you?"

        buttons = [
            [
                InlineKeyboardButton(
                    "📊 See my streak",
                    callback_data=f"{self.keys.streak}:{str(self.habit.id)}",
                )
            ],
            [
                InlineKeyboardButton(
                    "🖊 Log for another habit", callback_data=self.keys.id
                )
            ],
            self.main_menu_button,
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        update.callback_query.edit_message_text(text, reply_markup=keyboard)
        return self.keys.answer4

    def find_three_days(self, timezone):
        "returns today, yesterday, and the day before for the timezone"
        today = datetime.now(tz=utc) + timedelta(hours=timezone)
        today = today.date()
        pure_dates = [(today - timedelta(days=i)) for i in range(3)]
        readable_dates = self.readable_days(pure_dates)
        self.three_days = {pure_dates[i]: readable_dates[i] for i in range(3)}
        return self.three_days

    def readable_days(self, dates):
        "returns readable names for date buttons"
        readable = [
            f"Today ({dates[0].strftime('%a')})",
            f"Yesterday ({dates[1].strftime('%a')})",
            f"{dates[2].strftime('%A')}",
        ]
        return readable

    def create_date_buttons(self):
        self.date_buttons = []

        for date, name in self.three_days.items():
            record = crud.get_record(self.user.id, self.habit.id, date)
            callback_data = f"{self.keys.log_exists if record else ''}{str(date)}"
            button_text = f"{'✅ ' if record else '❌ '}{name}"
            button = InlineKeyboardButton(button_text, callback_data=callback_data)
            self.date_buttons.append([button])
        self.date_buttons.append(
            [InlineKeyboardButton(" I'm done, go back", callback_data=self.keys.done)]
        )

    def get_streak(self, update, context):
        habit_id = int(update.callback_query.data.split(":")[1])
        habit = crud.get_habit(habit_id, self.user.id)
        streak = habit.streak
        text = (
            f"📊You have a streak of <b>{streak} days </b> for {habit.name}.\n"
            "\n"
            f"{'Keep growing that number!' if streak>0 else 'Go get started!'}"
        )
        keyboard = InlineKeyboardMarkup([self.main_menu_button])

        update.callback_query.edit_message_text(
            text, reply_markup=keyboard, parse_mode="HTML"
        )
        return self.keys.main_menu
