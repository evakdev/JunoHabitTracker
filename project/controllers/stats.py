from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.ext.commandhandler import CommandHandler
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from controllers.base import Conversation
from controllers.mixins import ChooseHabitMixin
from controllers.mainkeys import stats


class Stats(ChooseHabitMixin, Conversation):
    def __init__(self):
        super().__init__()
        self.entry_points = [
            CommandHandler(stats, self.ask_habit),
            CallbackQueryHandler(self.ask_habit, pattern=self.keys.id),
        ]
        self.states = self.choose_habit_states | {
            self.keys.redo: [
                CallbackQueryHandler(self.ask_habit, pattern=self.keys.redo),
                self.main_menu_callback_state,
            ],
        }
        self.name = "Stats"
        self.create_handler()

    def add_keys(self):
        super().add_keys()
        self.keys.id = stats
        self.keys.redo = self.keys.id + "redo"

    def ask_habit(self, update, context):
        if self.user_doesnt_exist(update):
            return self.redirect_to_timezone(update, context)
        self.choose_habit_text = "Choose a habit to see a summary of your stats. 📊"
        return super().ask_habit(update, context)

    def get_habit(self, update, context):
        update_, context_ = super().get_habit(update, context)
        if self.habit.has_logs:
            return self.prepare_stats(update_, context_)
        return self.no_stats(update_, context_)

    def no_stats(self, update, context):
        text = "You haven't started this habit yet!"

        button = [
            InlineKeyboardButton("Choose another habit", callback_data=self.keys.redo)
        ]
        keyboard = InlineKeyboardMarkup([button, self.main_menu_button])

        update.callback_query.edit_message_text(text, reply_markup=keyboard)
        return self.keys.redo

    def prepare_stats(self, update, context):
        streak = self.habit.streak
        total_done_days = self.habit.total_done_days
        total_loggable_days = self.habit.total_loggable_days
        percentage_of_success = (total_done_days / total_loggable_days) * 100

        text = (
            f"<b> 📊 {self.habit.name}</b>\n"
            "\n"
            f"✅ Current Streak: <b>{streak}</b>\n"
            f"✅ Since you started, you've done this habit for <b>{total_done_days} </b> of your {total_loggable_days} chosen days.\n"
            f"✅ Your success percentage is <b>{round(percentage_of_success,ndigits=2)}%</b>!\n"
            "\n"
            "<em> Note: Your start date is the first day you logged for this habit.</em>"
        )

        keyboard = InlineKeyboardMarkup([self.main_menu_button])
        update.callback_query.edit_message_text(
            text, reply_markup=keyboard, parse_mode="HTML"
        )
        return self.keys.main_menu
