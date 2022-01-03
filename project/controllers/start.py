from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from telegram.ext.commandhandler import CommandHandler
from controllers.crud import get_user, create_user
from controllers.base import Conversation
from controllers.habitcreator import HabitCreator
from controllers.timezone import Timezone
from controllers.logger import Logger
from controllers.manager import Manager
from controllers.deletemydata import DeleteMyData
from controllers.stats import Stats
from controllers.feedback import Feedback


habitcreator = HabitCreator()
timezone = Timezone()
logger = Logger()
manager = Manager()
deletemydata = DeleteMyData()
stats = Stats()
feedback = Feedback()


class Start(Conversation):
    def __init__(self):
        super().__init__()
        self.entry_points = [
            CommandHandler("start", self.start),
            CommandHandler("main", self.main_menu),
        ]
        self.states = {
            self.keys.main_menu: [
                habitcreator.handler,
                timezone.handler,
                logger.handler,
                manager.handler,
                deletemydata.handler,
                stats.handler,
                feedback.handler,
                CommandHandler("start", self.start),
                # 👆 so that user can run /start after deleting all.
                # 👇 so that user can run shortcut commands.
                CommandHandler(habitcreator.keys.id, habitcreator.handler),
                CommandHandler(timezone.keys.edit, timezone.handler),
                CommandHandler(logger.keys.id, logger.handler),
                CommandHandler(manager.keys.id, manager.handler),
                CommandHandler(deletemydata.keys.id, deletemydata.handler),
                CommandHandler(stats.keys.id, stats.handler),
                CommandHandler(feedback.keys.id, feedback.handler),
            ],
            self.keys.ask_timezone: [
                CallbackQueryHandler(self.ask_timezone, pattern=self.keys.ask_timezone),
            ],
            self.keys.set_timezone: [
                timezone.handler,
                CallbackQueryHandler(
                    self.skip_timezone, pattern=self.keys.skip_timezone
                ),
            ],
        }
        self.name = "Main Menu"
        self.create_handler()

    def add_keys(self):
        super().add_keys()
        self.keys.id = "start"
        self.keys.initial_setup = self.keys.id + "initial_setup"
        self.keys.ask_timezone = self.keys.id + "asktimezone"
        self.keys.set_timezone = self.keys.id + "settimezone"
        self.keys.skip_timezone = self.keys.id + "skip_timezone"
        self.keys.timezone = timezone.keys.id

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
            "I'm Juno, your personal habit tracker! 🤖\n"
            "\n"
            "I help you create habits, mark them as done, and keep up your streak.\n"
            "\n"
            "Let's get started! 💪"
        )

        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="Start", callback_data=self.keys.ask_timezone)]]
        )
        update.message.reply_text(text=text, reply_markup=keyboard)
        return self.keys.ask_timezone

    def ask_timezone(self, update, context):
        text = (
            "⏲ Before we continue, I need to know your timezone offset.\n"
            "\n"
            "This helps me show you correct log dates, and generally avoid confusing you with our timezone difference. \n"
            "\n"
            "❗ if you don't feel comfortable sharing that, you can always use UTC +0. Just note that your dates might be shown wrongly.\n"
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
        update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
        return self.keys.set_timezone

    def skip_timezone(self, update, context):
        self.timezone = 0
        user = create_user(id=self.user_id, timezone=0)
        return self.main_menu(update, context)
