from telegram.ext import ConversationHandler
from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.ext.commandhandler import CommandHandler
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from controllers import mainkeys
from controllers.crud import get_user
from controllers.ptbshortcuts import get_from_user, send_message


# Base classes.
class Keys:
    def __init__(self):
        pass


class Conversation:
    """This is the base class for any button on the main menu.
    To add a button, you must add a new class that inherits from this class.
    You need to add the button itself in this class and connect it to the subclass
    by adding its id key to add_main_menu_keys().

    To make the conversation's handler, you need to define entry_points, states,
    additional fallbacks, map_to_parent, and name in __init__().
    Then run create_handler() to create the handler.
    """

    def __init__(self):
        self.entry_points = []
        self.states = {}
        self.fallbacks = []
        self.map_to_parent = {}
        self.name = ""

        self.add_keys()
        self.main_menu_button = [
            InlineKeyboardButton("↩ Main Menu", callback_data=self.keys.main_menu)
        ]
        self.main_menu_callback_state = CallbackQueryHandler(
            self.main_menu, pattern=self.keys.main_menu
        )
        self.main_menu_command_state = CommandHandler("main", self.main_menu)

    def add_keys(self):
        self.keys = Keys()
        self.keys.id = ""
        self.keys.end = -1
        self.keys.goback = "goback"  # for returning to the previous conversation, when previous conversation is not the main menu
        self.add_main_menu_keys()
        self.add_menu_specific_keys()

    def redirect_to_timezone(self, update, context):
        text = (
            "⚠ You need to enter a timezone before you can use this bot.\n"
            "Please click on /start and follow instructions there first."
        )
        send_message(update, text)
        return self.keys.end

    def user_doesnt_exist(self, update):
        user_id = get_from_user(update).id
        user = get_user(user_id)
        if user:
            return False
        return True

    def add_menu_specific_keys(self):
        self.keys.main_menu = "main_menu"  # this is the default key for the main menu
        self.keys.methodend = "methodend"  # for returning after methodcreation

    def add_main_menu_keys(self):
        """NOTE: All keys here except main_menu have been taken from different nested conversation's id keys.
        If you change id keys for any reason, you have to change them here MANUALLY."""

        self.keys.manager = mainkeys.manager
        self.keys.log = mainkeys.log
        self.keys.stats = mainkeys.stats
        self.keys.create = mainkeys.create
        self.keys.edit_timezone = mainkeys.edit_timezone
        self.keys.deletemydata = mainkeys.deletemydata

    def create_handler(self):
        """Function to create a conversation handler that includes the basic attributes
        needed for every menu button. define conversation-specific attributes in init and
        then run this. default attributes and conversation-specific attributes will be
        combined.
        """
        states = self.states
        if self.keys.id != "start":
            states = states | {self.keys.main_menu: [self.main_menu_callback_state]}
        entry_points = self.entry_points
        fallbacks = self.fallbacks + [CommandHandler("main", self.main_menu)]
        map_to_parent = self.map_to_parent | {self.keys.end: self.keys.main_menu}
        name = self.name

        self.handler = ConversationHandler(
            entry_points=entry_points,
            states=states,
            fallbacks=fallbacks,
            map_to_parent=map_to_parent,
            name=name,
        )

    def main_menu(self, update, context):
        if self.user_doesnt_exist(update):
            return self.redirect_to_timezone(update, context)
        text = (
            "You can see your current habits, log for them, see stats, or create new ones.\n"
            "\n"
            "💡 At any point, send /main to end the conversation and return to this menu. \n"
            "💡 Type <code>/</code> to see the list of shortcut commands.\n"
            "\n"
            "❗ Don't forget to change your timezone if Daylight Saving has recently applied!\n"
        )
        buttons = [
            [
                InlineKeyboardButton("Log for a Habit", callback_data=self.keys.log),
                InlineKeyboardButton("See Stats", callback_data=self.keys.stats),
            ],
            [
                InlineKeyboardButton("Manage Habits", callback_data=self.keys.manager),
                InlineKeyboardButton(
                    "Create a New Habit", callback_data=self.keys.create
                ),
            ],
            [
                InlineKeyboardButton(
                    "Edit Timezone", callback_data=self.keys.edit_timezone
                ),
                InlineKeyboardButton(
                    "Delete all my data", callback_data=self.keys.deletemydata
                ),
            ],
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        try:
            update.callback_query.edit_message_text(
                text=text, reply_markup=keyboard, parse_mode="HTML"
            )
        except:
            update.message.reply_text(
                text=text, reply_markup=keyboard, parse_mode="HTML"
            )

        # for nested conversations, we need to return end to get back
        # to the parent. The only exception is start, where we'll return
        # self.keys.main_menu to stay in the conversation.

        if self.keys.id == "start":
            return self.keys.main_menu
        return self.keys.end
