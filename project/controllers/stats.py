import telegram
from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.ext.conversationhandler import ConversationHandler
from telegram.ext.commandhandler import CommandHandler
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from controllers.base import Conversation
from controllers.mixins import ChooseHabitMixin, MainMenuMixin


class Stats(MainMenuMixin, ChooseHabitMixin, Conversation):
    def __init__(self):
        super().__init__()
        self.handler = ConversationHandler(
            entry_points=[
                CommandHandler("stats", self.ask_habit),
                CallbackQueryHandler(self.ask_habit, pattern=self.keys.id),
            ],
            states=self.choose_habit_states | self.main_menu_states | {},
            fallbacks=[CommandHandler(self.keys.cancel, self.cancel)],
            map_to_parent={self.keys.end: self.keys.main_menu},
            name="Stats",
        )

    def add_keys(self):
        super().add_keys()
        self.keys.id = "stats"
        self.keys.answer1 = self.keys.id + "1"

    def main_menu(self, update, context):
        super().main_menu(update, context)
        return self.keys.end

    def ask_habit(self, update, context):
        self.choose_habit_text = "Choose a habit to see a summary of your stats. 📊"
        return super().ask_habit(update, context)

    def get_habit(self, update, context):
        update_, context_ = super().get_habit(update, context)
        return self.prepare_stats(update_, context_)

    def prepare_stats(self, update, context):
        streak = self.habit.streak
        total_done_days = self.habit.total_done_days
        total_loggable_days = self.habit.total_loggable_days
        percentage_of_success = (total_done_days / total_loggable_days) * 100

        text = (
            f"<b> 📊 {self.habit.name}</b>\n"
            "\n"
            f"Current Streak: <b>{streak}</b>\n"
            f"Since you started, you've done this habit for <b>{total_done_days} </b> of the {total_loggable_days} possible days.\n"
            f"Your success percentage is <b>{percentage_of_success}%</b>!"
        )
        keyboard = InlineKeyboardMarkup([self.main_menu_button])
        update.callback_query.edit_message_text(
            text, reply_markup=keyboard, parse_mode=telegram.ParseMode.HTML
        )
        return self.keys.main_menu
