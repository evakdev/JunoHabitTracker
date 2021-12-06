from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.ext.conversationhandler import ConversationHandler
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.filters import Filters
from telegram.ext.messagehandler import MessageHandler
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from controllers.crud import edit_habit, delete_habit, add_method, find_habit_by_name
from controllers.base import Conversation
from controllers.methodcreator import MethodCreator
from controllers.mixins import MainMenuMixin, ChooseHabitMixin

methodcreator = MethodCreator()


class Manager(MainMenuMixin, ChooseHabitMixin, Conversation):
    def __init__(self):
        super().__init__()
        self.handler = ConversationHandler(
            entry_points=[
                CommandHandler("manage", self.ask_habit),
                CallbackQueryHandler(self.ask_habit, pattern=self.keys.id),
            ],
            states=self.choose_habit_states
            | self.main_menu_states
            | {
                self.keys.answer2: [
                    CallbackQueryHandler(self.ask_rename, pattern=self.keys.rename),
                    methodcreator.handler,
                    CallbackQueryHandler(self.ask_delete, pattern=self.keys.delete),
                    CallbackQueryHandler(self.main_menu, pattern=self.keys.main_menu),
                ],
                self.keys.answer3: [MessageHandler(Filters.text, self.get_rename)],
                self.keys.answer4: [
                    CallbackQueryHandler(
                        self.get_delete, pattern=self.keys.deleteconfirm
                    ),
                    CallbackQueryHandler(self.ask_task, pattern=self.keys.id),
                ],
                self.keys.goback: [
                    CallbackQueryHandler(self.ask_habit, pattern=self.keys.goback)
                ],
                self.keys.redo: [
                    CallbackQueryHandler(self.ask_habit, pattern=self.keys.id)
                ],
                self.keys.main_menu: [
                    CallbackQueryHandler(self.main_menu, pattern=self.keys.main_menu)
                ],
            },
            fallbacks=[CommandHandler(self.keys.cancel, self.cancel)],
            map_to_parent={self.keys.end: self.keys.main_menu},
            name="Manager",
        )

    def add_keys(self):
        super().add_keys()
        self.keys.id = "manager"
        self.keys.answer1 = self.keys.id + "1"
        self.keys.answer2 = self.keys.id + "2"
        self.keys.answer3 = self.keys.id + "3"
        self.keys.answer4 = self.keys.id + "4"
        self.keys.answer5 = self.keys.id + "5"
        self.keys.redo = self.keys.id + "redo"
        self.keys.rename = self.keys.id + "rename"
        self.keys.delete = self.keys.id + "delete"
        self.keys.changemethod = self.keys.id + "changemethod"
        self.keys.deleteconfirm = self.keys.id + "deleteconfirm"

    def main_menu(self, update, context):
        super().main_menu(update, context)
        return self.keys.end

    def ask_habit(self, update, context):
        return super().ask_habit(update, context)

    def get_habit(self, update, context):
        update_, context_ = super().get_habit(update, context)
        return self.ask_task(update_, context_)

    def ask_task(self, update, context):
        text = "What do you want to do?"
        buttons = [
            [InlineKeyboardButton("Rename", callback_data=self.keys.rename)],
            [
                InlineKeyboardButton(
                    "Change tracking method", callback_data=methodcreator.keys.id
                )
            ],
            [
                InlineKeyboardButton(
                    "Delete this habit and all its data", callback_data=self.keys.delete
                )
            ],
            self.main_menu_button,
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        update.callback_query.edit_message_text(text, reply_markup=keyboard)
        return self.keys.answer2

    def ask_rename(self, update, context):
        text = f"Enter a new name for {self.habit.name}"
        update.callback_query.edit_message_text(text)
        return self.keys.answer3

    def get_rename(self, update, context):
        self.new_name = "".join(update.message.text).capitalize()
        if self.habit_exists(self.new_name):
            return self.duplicate_habit(update, context)
        old_name = self.habit.name
        edit_habit(self.habit, name=self.new_name)
        print(self.habit.name)
        text = f"Successfully changed {old_name} to {self.new_name}."
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("↩ Go back", callback_data=self.keys.id)]]
        )
        update.message.reply_text(text, reply_markup=keyboard)
        return self.keys.redo

    def duplicate_habit(self, update, context):
        text = (
            f"You already have a habit named {self.new_name}!\n"
            "Enter a new name, or go back to edit the other {self.new_name} instead.\n"
        )
        buttons = [[InlineKeyboardButton("Go back", callback_data=self.keys.redo)]]
        keyboard = InlineKeyboardMarkup(buttons)
        update.message.reply_text(text, keyboard)
        return self.keys.answer4

    def habit_exists(self, name):
        habit = find_habit_by_name(name, self.user.id)
        return bool(habit)

    def get_method(self, update, context):
        method = context.user_data.get("method")
        add_method(self.habit, method)
        text = "Successfully changed your tracking method."
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("↩ Go back", callback_data=self.keys.id)]]
        )
        update.callback_query.edit_message_text(text, reply_markup=keyboard)
        return self.keys.redo

    def ask_delete(self, update, context):
        text = (
            f"This will delete everything you have tracked for {self.habit.name}, and completey remove it from the database.\n "
            "Are you sure you want to do this?"
        )
        buttons = [
            [
                InlineKeyboardButton(
                    "Yes, delete it", callback_data=self.keys.deleteconfirm
                )
            ],
            [InlineKeyboardButton("No, go back", callback_data=self.keys.id)],
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        update.callback_query.edit_message_text(text, reply_markup=keyboard)
        return self.keys.answer4

    def get_delete(self, update, context):
        name = self.habit.name
        delete_habit(self.habit)
        self.habit = None
        text = f"Successfully deleted {name} and all its records."
        keyboard = InlineKeyboardMarkup(self.main_menu_button)
        update.callback_query.edit_message_text(text, reply_markup=keyboard)
        return self.keys.main_menu
