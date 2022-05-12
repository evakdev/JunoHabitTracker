from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.ext.commandhandler import CommandHandler
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from controllers.base import Conversation
from controllers.mixins import ChooseHabitMixin
from controllers.mainkeys import stats
from controllers.crud import get_method


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

    def num_with_unit(self, num, unit):
        if num == 1:
            return f"{num} {unit}"
        return f"{num} {unit}s"

    def prepare_stats(self, update, context):
        streak_unit = get_method(self.habit.method).duration

        text = (
            f"<b> 📊 {self.habit.name}</b>\n"
            "\n"
            f"<b>✅ Current Streak: {self.num_with_unit(self.habit.streak,streak_unit)}</b>\n"
            "\n"
            "<b>✅ Done Days:</b>\n"
            f"<em>     - This week: {self.num_with_unit(self.habit.done_this_week,'day')}</em>\n"
            f"<em>     - This month: {self.num_with_unit(self.habit.done_this_month,'day')}</em>\n"
            f"<em>     - Total: {self.num_with_unit(self.habit.total_done_days,'day')}</em>\n"
            "\n"
            "<em>Notes:\n"
            "For now, I only work with Gregorian calendar, and assume week start day is Monday.</em>"
        )

        if streak_unit != "day":
            notes = (
                "<em> Notes:\n"
                "If the first week/month did not have enough days for you to be able to reach your goal, "
                "then it will still be counted in your streak. But only if you reach the percentage of goal that "
                "was possible to do. e.g. Say you started on friday and had a goal of 4 times a week. you logged for"
                "Fri,Sat, and Sun. it's not 4 days, but it counts as streak because you did all that was possible to do."
            )

        keyboard = InlineKeyboardMarkup([self.main_menu_button])
        print("here")
        update.callback_query.edit_message_text(
            text, reply_markup=keyboard, parse_mode="HTML"
        )
        print("or here?")
        return self.keys.main_menu
