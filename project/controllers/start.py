from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.conversationhandler import ConversationHandler
from controllers.crud import get_user, create_user
from controllers.base import Conversation
from controllers.mixins import MainMenuMixin
from controllers.habitcreator import HabitCreator
from controllers.timezone import Timezone
from controllers.logger import Logger
from controllers.manager import Manager
from controllers.deletemydata import DeleteMyData
from controllers.stats import Stats

habitcreator = HabitCreator()
timezone = Timezone()
logger = Logger()
manager = Manager()
deletemydata = DeleteMyData()
stats = Stats()


class Start(MainMenuMixin, Conversation):
    def __init__(self):
        super().__init__()
        self.handler = ConversationHandler(
            entry_points=[
                CommandHandler("start", self.start),
                CommandHandler("main", self.main_menu),
            ],
            states={
                self.keys.goback: [
                    CallbackQueryHandler(self.main_menu, pattern=self.keys.goback)
                ],
                self.keys.main_menu: [
                    habitcreator.handler,
                    timezone.handler,
                    logger.handler,
                    manager.handler,
                    deletemydata.handler,
                    stats.handler,
                    CommandHandler(
                        "start", self.start
                    ),  # so that user can run /start after deleting all.
                ],
                self.keys.timezone: [
                    timezone.handler,
                    CallbackQueryHandler(
                        self.skip_timezone, pattern=self.keys.skip_timezone
                    ),
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
            name="Main Menu",
        )

    def add_keys(self):
        super().add_keys()
        self.keys.initial_setup = "initial_setup"
        self.keys.timezone = "timezone"
        self.keys.skip_timezone = "skip_timezone"

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

    def skip_timezone(self, update, context):
        self.timezone = 0
        user = create_user(id=self.user_id, timezone=0)
        return self.main_menu(update, context)
