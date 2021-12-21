from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from controllers import crud
from telegram.ext import CallbackQueryHandler
from controllers.ptbshortcuts import send_message, get_from_user


class ChooseHabitMixin:
    "A Mixin to use when user needs to choose one of their habits to continue."

    choose_habit_key = "choosehabit"
    choose_habit_text = "Please choose a habit to edit."

    @property
    def choose_habit_states(self):
        states = {
            self.choose_habit_key: [
                CallbackQueryHandler(self.get_habit, pattern="^[0-9]+:[0-9]+$"),
                self.main_menu_callback_state,
            ],
        }
        return states

    def ask_habit(self, update, context):
        keyboard = self.get_habit_keyboard(get_from_user(update).id)

        if keyboard:
            send_message(update, self.choose_habit_text, reply_markup=keyboard)
            return self.choose_habit_key
        return self.no_habit(update, context)

    def get_habit(self, update, context):
        "Sets self.habit and self.user. returns update and context."
        user_id, habit_id = map(int, update.callback_query.data.split(":"))
        self.habit = crud.get_habit(habit_id, user_id)
        self.user = crud.get_user(user_id)
        if not self.habit:
            return self.wrong_habit(update, context)
        return update, context

    def get_habit_keyboard(self, user_id):

        user = crud.get_user(user_id)
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
        send_message(update, text, reply_markup=keyboard)
        return self.keys.main_menu

    def wrong_habit(self, update, context):
        text = "I don't know that habit. Please try again."
        keyboard = (InlineKeyboardMarkup(self.habit_buttons),)
        update.callback_query.edit_message_text(text, reply_markup=keyboard)
        return self.choose_habit_key
