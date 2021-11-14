from telegram import replymarkup
from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.ext.filters import Filters
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from telegram.replykeyboardmarkup import ReplyKeyboardMarkup
from base import dispatcher
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.conversationhandler import ConversationHandler
from telegram.ext.messagehandler import MessageHandler
from enum import IntEnum

from controllers.crud import create_method




class Types(IntEnum):
    everyday, interval, count, specified = 1, 2, 3, 4


class Steps(IntEnum):
    TYPECHOICE = 5
    SELECTTYPE = 6
    DURATIONCHOICE, DURATIONHANDLER = 7, 8
    INTERVALDECISION, INTERVALHANDLER = 9, 10
    COUNTDECISION, COUNTHANDLER = 11, 12
    SPECIFIEDDECISION = 13
    CANCEL = 14
    DONE = 15


# durations
WEEK, MONTH = "week", "month"
END = ConversationHandler.END
METHODCHOICEEND= 'methodchoiceend'

class HelperFunctions:
    def get_method_type(type_value):
        type_value = int(type_value)
        if type_value == Types.everyday:
            return Types.interval.name

        for i in Types:
            if i.value == type_value:
                return i.name

    def make_specified_buttons(duration):

        if duration == WEEK:
            buttons = [
                [InlineKeyboardButton("Monday", callback_data="day1")],
                [InlineKeyboardButton("Tuesday", callback_data="day2")],
                [InlineKeyboardButton("Wednesday", callback_data="day3")],
                [InlineKeyboardButton("Thursday", callback_data="day4")],
                [InlineKeyboardButton("Friday", callback_data="day5")],
                [InlineKeyboardButton("Saturday", callback_data="day6")],
                [InlineKeyboardButton("Sunday", callback_data="day7")],
                [InlineKeyboardButton("Done", callback_data="done")],
            ]
        elif duration == MONTH:

            buttons = [
                [
                    InlineKeyboardButton(str(i + j), callback_data=f"day{i+j}")
                    for j in range(1, 6)
                ]
                for i in range(0, 26, 5)
            ]
            buttons.append([InlineKeyboardButton("Done", callback_data="done")])

        return buttons
    def update_specified_days_list(context, choice):
        days = context.user_data.get("method").get("specified", list())
        clean_choice = int(choice.replace("day", ""))
        if clean_choice in days:
            days.remove(clean_choice)
        else:
            days.append(clean_choice)
        return days 
    def update_specified_button_texts(buttons, choice):
        def is_checked(button):
            return button.text.startswith("✅")

        for i, row in enumerate(buttons):
            for j, button in enumerate(row):
                if button.callback_data != choice: 
                    continue
                if is_checked(button):
                    text = button.text.replace("✅", "")
                else:
                    text = button.text = "✅ " + button.text
                buttons[i][j] = InlineKeyboardButton(text, callback_data=button.callback_data)
                return buttons
        return buttons


def select_type(update, context):
    buttons = [
        [InlineKeyboardButton("Every day", callback_data=Types.everyday)],
        [InlineKeyboardButton("Every X days", callback_data=Types.interval)],
        [InlineKeyboardButton("X days a week/month", callback_data=Types.count)],
        [
            InlineKeyboardButton(
                "Specific days of the week/month", callback_data=Types.specified
            )
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    text = "how often do you want to do this habit?"
    update.callback_query.edit_message_text(text, reply_markup=keyboard)
    return Steps.TYPECHOICE


def everyday(update, context):
    method_dict = {
        "type": HelperFunctions.get_method_type(update.callback_query.data),
        "duration": "month",
        "interval": 0,
    }
    context.user_data["method"] = method_dict
    return done(update, context)


def interval_decision(update, context):
    method_dict = {
        "type": HelperFunctions.get_method_type(update.callback_query.data),
        "duration": "month",
    }
    context.user_data["method"] = method_dict
    text = "How many days do you wanna have in between?\n(e.g. 1 means you do it every 2 days.)"
    update.callback_query.edit_message_text(text)
    return Steps.INTERVALHANDLER


def interval_handler(update, context):
    # should have a pattern of numbers.
    days = int(update.message.text)
    context.user_data["method"]["interval"] = days
    return done(update, context)


def duration_choice(update, context):
    method_dict = {"type": HelperFunctions.get_method_type(update.callback_query.data)}
    context.user_data["method"] = method_dict
    text = "Do you want to track based on the week, or the month?"
    buttons = [
        [
            InlineKeyboardButton("Week", callback_data=WEEK),
            InlineKeyboardButton("Month", callback_data=MONTH),
        ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    update.callback_query.edit_message_text(text, reply_markup=keyboard)
    return Steps.DURATIONHANDLER


def duration_handler(update, context):
    choice = update.callback_query.data
    if not choice in [WEEK, MONTH]:
        return Steps.CANCEL
    context.user_data.get("method")["duration"] = choice
    type_funcs = {
        Types.count.name: count_decision,
        Types.specified.name: specified_decision,
    }
    return type_funcs.get(context.user_data.get("method").get("type"))(update, context)


def count_decision(update, context):
    text = "How many times do you want to do this habit?"
    update.callback_query.edit_message_text(text)
    return Steps.COUNTHANDLER


def count_handler(update, context):
    count = int(update.message.text)
    context.user_data.get("method")["count"] = count
    return done(update, context)


def specified_decision(update, context):
    if update.callback_query.data == "done":
        return done(update, context)

    duration = context.user_data.get("method").get("duration")
    text = f"Which days of the {duration} do you want to do this habit?"
    current_buttons = context.user_data.get("buttons")
    if not current_buttons:
        buttons = HelperFunctions.make_specified_buttons(duration)
    else:
        choice = update.callback_query.data
        context.user_data.get("method")["specified"] = HelperFunctions.update_specified_days_list(context, choice)
        buttons = HelperFunctions.update_specified_button_texts(current_buttons, choice)

    context.user_data["buttons"] = buttons
    keyboard = InlineKeyboardMarkup(buttons)
    update.callback_query.edit_message_text(text, reply_markup=keyboard)

    return Steps.SPECIFIEDDECISION


def done(update, context):
    method = create_method(**context.user_data.get("method"))
    context.user_data.get("habit")['method'] = method
    text = "All done! Click the button to save your new habit."
    button = [InlineKeyboardButton('Save', callback_data='save')]
    keyboard = InlineKeyboardMarkup([button])
    try: update.message.reply_text(text, reply_markup=keyboard)
    except: update.callback_query.edit_message_text(text,reply_markup=keyboard)
    return END


def cancel(update, context):
    update.callback_query.edit_message_text("Canceling Command.")


everyday_convo = ConversationHandler(
    entry_points=[CallbackQueryHandler(everyday, pattern=f"^{Types.everyday}$")],
    states={
        Steps.DONE: [CallbackQueryHandler(done, pattern=f"^{Types.everyday}$")],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    map_to_parent={END:END}
)


interval_convo = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(interval_decision, pattern=f"^{Types.interval}$")
    ],
    states={
        Steps.INTERVALHANDLER: [
            MessageHandler(Filters.regex("[1-9]+"), interval_handler)
        ]
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    map_to_parent={END:END}
)


count_convo = ConversationHandler(
    entry_points=[CallbackQueryHandler(duration_choice, pattern=f"^{Types.count}$")],
    states={
        Steps.DURATIONHANDLER: [
            CallbackQueryHandler(duration_handler, pattern=f"^{WEEK}|{MONTH}$")
        ],
        Steps.COUNTHANDLER: [MessageHandler(Filters.regex("[1-9]+"), count_handler)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    map_to_parent={END:END},
)


specified_convo = ConversationHandler(
    entry_points=[CallbackQueryHandler(duration_choice, pattern=f"^{Types.specified}")],
    states={
        Steps.DURATIONHANDLER: [
            CallbackQueryHandler(duration_handler, pattern=f"^{WEEK}|{MONTH}$")
        ],
        Steps.SPECIFIEDDECISION: [
            CallbackQueryHandler(specified_decision, pattern=f"^day[1-9]+|done$")
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    map_to_parent={END:END}
)


method_convo_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(select_type, pattern="^next$")],
    states={
        Steps.TYPECHOICE: [everyday_convo, interval_convo, count_convo, specified_convo]
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    map_to_parent={'test': METHODCHOICEEND,
                   END: METHODCHOICEEND},
    name ='method convo handler'
)


