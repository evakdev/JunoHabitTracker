from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.ext.filters import Filters
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.messagehandler import MessageHandler
from controllers.crud import create_habit, get_user, create_method
from controllers.methodcreator import MethodCreator
from controllers.base import Conversation
from controllers.mainkeys import create
from controllers.ptbshortcuts import send_message

methodcreator = MethodCreator()


class HabitCreator(Conversation):
    def __init__(self):
        super().__init__()
        self.entry_points = [
            CallbackQueryHandler(self.ask_name, pattern=f"^{self.keys.id}$"),
            CommandHandler(create, self.ask_name),
        ]
        self.states = {
            self.keys.answer1: [
                self.main_menu_command_state,
                MessageHandler(Filters.regex("[/]+"), callback=self.filter_error),
                # 👆 so that commands are not accepted as habit names
                MessageHandler(Filters.text, callback=self.get_name),
            ],
            self.keys.answer2: [methodcreator.handler],
            self.keys.answer3: [
                self.main_menu_callback_state,
                CallbackQueryHandler(self.ask_name, pattern=f"^{self.keys.id}$"),
            ],
            self.keys.methodend: [
                CallbackQueryHandler(self.save, pattern=f"^{self.keys.methodend}$")
                # This comes back from method handler.
            ],
        }

        self.name = "Habit Creator"
        self.create_handler()

    def add_keys(self):
        super().add_keys()
        self.keys.id = create
        self.keys.answer1 = self.keys.id + "1"
        self.keys.answer2 = self.keys.id + "2"
        self.keys.answer3 = self.keys.id + "3"

    def ask_name(self, update, context):
        if self.user_doesnt_exist(update):
            return self.redirect_to_timezone(update, context)
        text = "What should we name your new habit?"
        send_message(update, text)
        return self.keys.answer1

    def get_name(self, update, context):
        self.user_id = update.message.from_user.id
        self.habit_name = update.message.text
        user = get_user(self.user_id)

        if user.habit_name_is_duplicate(self.habit_name):
            return self.duplicate_habit(update, context)
        return self.ask_method(update, context)

    def duplicate_habit(self, update, context):
        text = (
            f"Looks like you already have a habit named {self.habit_name}!\n"
            "go to /manage to edit it if you want, or enter a new name."
        )
        update.message.reply_text(text)
        return self.keys.answer1

    def ask_method(self, update, context):

        text = "Awesome. Now let's see how you want to track this habit..."
        button = InlineKeyboardButton("Continue", callback_data=methodcreator.keys.id)
        keyboard = InlineKeyboardMarkup([[button]])
        update.message.reply_text(text, reply_markup=keyboard)
        return self.keys.answer2

    def filter_error(self, update, context):
        text = (
            "Sorry, you can't use / here, that's reserved for bot commands.\n"
            "please send another name.\n"
            "Or if you wanted to exit this menu, use /main."
        )
        update.message.reply_text(text)
        return self.keys.answer1

    def save(self, update, context):
        method = create_method(**context.user_data.get("method"))
        habit = create_habit(self.habit_name, self.user_id, method.id)

        text = (
            "All done!\n"
            f"Starting from now, you can start logging for {self.habit_name}.\n"
            "\n"
            "Now go get it done! 💪"
        )
        buttons = [
            [InlineKeyboardButton("Create another", callback_data=self.keys.id)],
            self.main_menu_button,
        ]

        keyboard = InlineKeyboardMarkup(buttons)
        update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
        return self.keys.answer3

    def confirm_exit(self, update, context):
        """This is necessary because menu buttons won't work if user sends /main in methodcreator."""
        text = "Click to go back."
        keyboard = InlineKeyboardMarkup([self.main_menu_button])
        send_message(update, text, reply_markup=keyboard)
        return self.keys.end
