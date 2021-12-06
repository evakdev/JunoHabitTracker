from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from controllers.crud import get_user, get_habit
from controllers.base import Conversation
from telegram.ext import CallbackQueryHandler


class MainMenuMixin(Conversation):
    def __init__(self):
        super().__init__()
        self.add_keys()
        self.main_menu_key = "main_menu"
        self.main_menu_button = [
            InlineKeyboardButton("↩ Main Menu", callback_data=self.keys.main_menu)
        ]
        self.main_menu_states = {
            self.keys.main_menu: [
                CallbackQueryHandler(self.main_menu, pattern=self.keys.main_menu),
            ],
        }

    def add_keys(self):
        """NOTE: All keys here except main_menu have been taken from different nested conversation's id keys.
        If you change id keys for any reason, you have to change them here MANUALLY."""
        super().add_keys()
        self.keys.main_menu = "main_menu"
        self.keys.manager = "manager"
        self.keys.log = "logger"
        self.keys.stats = "stats"
        self.keys.create = "habitcreator"
        self.keys.edit_timezone = "timezoneedit"
        self.keys.deletemydata = "deletemydata"

    def main_menu(self, update, context):
        text = (
            "You can see your current habits, log for them, see stats, or create new ones.\n"
            "Change your timezone if Daylight Saving has recently applied.\n"
            "at any point, you can send /main to return to this menu.\n"
        )
        buttons = [
            [
                InlineKeyboardButton("✔ Log for a Habit", callback_data=self.keys.log),
                InlineKeyboardButton("See Stats", callback_data=self.keys.stats),
            ],
            [
                InlineKeyboardButton(
                    "✔ Manage Habits", callback_data=self.keys.manager
                ),
                InlineKeyboardButton(
                    "✔ Create a New Habit", callback_data=self.keys.create
                ),
            ],
            [
                InlineKeyboardButton(
                    "✔ Edit Timezone", callback_data=self.keys.edit_timezone
                ),
                InlineKeyboardButton(
                    "✔ Delete all my data", callback_data=self.keys.deletemydata
                ),
            ],
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        try:
            update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
        except:
            update.message.reply_text(text=text, reply_markup=keyboard)
        return self.keys.main_menu


class ChooseHabitMixin:
    def __init__(self):
        "Note: Needs MainMenu Mixin for some functionality."
        self.choose_habit_key = "choosehabit"
        self.choose_habit_text = "Please choose a habit to edit."

        self.choose_habit_states = {
            self.choose_habit_key: [
                CallbackQueryHandler(self.get_habit, pattern="^[0-9]+:[0-9]+$"),
                CallbackQueryHandler(self.main_menu, pattern="main_menu"),
            ],
        }

    def ask_habit(self, update, context):
        keyboard = self.get_habit_keyboard(update.callback_query.from_user.id)
        if keyboard:
            update.callback_query.edit_message_text(
                self.choose_habit_text, reply_markup=keyboard
            )
            return self.choose_habit_key
        return self.no_habit(update, context)

    def get_habit(self, update, context):
        "Sets self.habit and self.user. returns update and context."
        user_id, habit_id = map(int, update.callback_query.data.split(":"))
        self.habit = get_habit(habit_id, user_id)
        self.user = get_user(user_id)
        if not self.habit:
            return self.wrong_habit(update, context)
        return update, context

    def get_habit_keyboard(self, user_id):
        user = get_user(user_id)
        user_habits = user.get_habits()
        if not user_habits:
            return None
        self.create_habit_buttons(user_habits)
        keyboard = InlineKeyboardMarkup(self.habit_buttons)
        return keyboard

    def create_habit_buttons(self, habits):
        row_count = len(habits) // 3
        if len(habits) % 3 != 0:
            row_count += 1

        self.habit_buttons = []
        row_num = 0
        row = []
        for habit in habits:
            callback_data = f"{str(habit.user)}:{str(habit.id)}"
            button = InlineKeyboardButton(habit.name, callback_data=callback_data)
            if len(row) < 2:
                row.append(button)
            else:
                self.habit_buttons.append(row.copy())
                row_num += 1
                row = []
                row.append(button)
            if habit == habits[-1]:
                self.habit_buttons.append(row.copy())
        self.habit_buttons.append(self.main_menu_button)

    def no_habit(self, update, context):
        text = (
            "You don't have any habits right now.\n"
            "Go back to the main menu and create one!"
        )
        keyboard = InlineKeyboardMarkup([self.main_menu_button])
        update.callback_query.edit_message_text(text, reply_markup=keyboard)
        return self.keys.main_menu

    def wrong_habit(self, update, context):
        text = "I don't know that habit. Please try again."
        keyboard = (InlineKeyboardMarkup(self.habit_buttons),)
        update.callback_query.edit_message_text(text, reply_markup=keyboard)
        return self.choose_habit_key
