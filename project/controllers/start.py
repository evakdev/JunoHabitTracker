from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.conversationhandler import ConversationHandler
from controllers.crud import get_user
from controllers.habitcreator import HabitCreator
from controllers.base import Conversation
from controllers.crud import create_user
from controllers.timezone import Timezone
from controllers.logger import Logger

habitcreator = HabitCreator()
timezone = Timezone()
logger = Logger()

class MainMenu(Conversation):
    def __init__(self):
        super().__init__()
        self.handler = ConversationHandler(
            entry_points=[
                CommandHandler("start", self.start),
                CommandHandler("main", self.main_menu),
                ],
            states={
                self.keys.backtomain: [CallbackQueryHandler(self.main_menu, pattern=self.keys.backtomain)],
                self.keys.main_menu: [
                    habitcreator.handler,
                    timezone.handler,
                    logger.handler,
                    ],
                self.keys.timezone: [
                    timezone.handler,
                    CallbackQueryHandler(self.skip_timezone,pattern=self.keys.skip_timezone)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            name = "Main Menu"
        )

    def add_keys(self):
        super().add_keys()
        self.keys.initial_setup = "initial_setup"
        self.keys.main_menu = "main_menu"
        self.keys.manage = "manage"
        self.keys.log = logger.keys.id
        self.keys.stats = "stats"
        self.keys.create = habitcreator.keys.id
        self.keys.timezone = timezone.keys.id
        self.keys.edit_timezone = timezone.keys.edit
        self.keys.skip_timezone = "skip_timezone"
        self.keys.delete_all = "delete_all"

    def start(self, update, context):
        self.user_id = update.message.from_user.id
        self.user_name = update.message.from_user.first_name
        user = get_user(self.user_id)
        if user:
            return self.main_menu(update, context)
        return self.welcome(update, context)

    def welcome(self, update, context):
        text = (
            f"Hi there {self.user_name}! 👋\n"
            "I'm Juno, your personal habit tracker!\n"
            "\n"
            "You can add as many habits as you want, decide how often you want to do them, and keep up your streak.\n"
            "I'll help you with that! 🤖\n"
        )
        update.message.reply_text(text=text)
        text = "Let's get started!"
        update.message.reply_text(text=text)
        text = (
            "In order to start, I need to know your timezone offset.\n"
            "\n"
            "This helps me show you correct log dates, and generally avoid confusing you with our timezone difference. \n"
            "\n"
            "if you don't feel comfortable sharing that, you can always use UTC +0. Just note that your dates might be shown wrongly.\n"
        )
        buttons = [
            [
                InlineKeyboardButton(
                    "Set My Timezone", callback_data=self.keys.timezone
                ),
                InlineKeyboardButton(
                    "Set it to UTC +0", callback_data=self.keys.skip_timezone
                ),
            ]
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        update.message.reply_text(text=text, reply_markup=keyboard)
        return self.keys.timezone


    def main_menu(self, update, context):
        text = (
            "You can see your current habits, log for them, see stats, or create new ones.\n"
            "Change your timezone if Daylight Saving has recently applied.\n"
            "at any point, you can send /main to return to this menu.\n"
        )
        buttons = [
            [
                InlineKeyboardButton("⏺ Log for a Habit", callback_data=self.keys.log),
                InlineKeyboardButton("See Stats", callback_data=self.keys.stats),
            ],
            [
                InlineKeyboardButton("Manage Habits", callback_data=self.keys.manage),
                InlineKeyboardButton(
                    "✔ Create a New Habit", callback_data=self.keys.create
                ),
            ],
            [
                InlineKeyboardButton("✔ Edit Timezone", callback_data=self.keys.edit_timezone),
                InlineKeyboardButton(
                    "Delete all my data", callback_data=self.keys.delete_all
                ),
            ],
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        try:
            update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
        except:
            update.message.reply_text(text=text, reply_markup=keyboard)
        return self.keys.main_menu


    def skip_timezone(self, update, context):
        self.timezone = 0
        user = create_user(id=self.user_id, timezone=0)
        return self.main_menu(update, context)