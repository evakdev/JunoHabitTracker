from telegram import replymarkup


def send_message(update, text, reply_markup=None, parse_mode=None):
    """
    Sends a message to the user.
    This will use callback_query.edit_message_text as priority. if it doesn't work, will use message.reply_text instead.
    To be used when we're not sure which one will be used.
    """
    try:
        return update.callback_query.edit_message_text(
            text, reply_markup=reply_markup, parse_mode=parse_mode
        )
    except:
        return update.message.reply_text(
            text, reply_markup=reply_markup, parse_mode=parse_mode
        )


def get_from_user(update):
    "returns from_user from either callback_query or message. Priority is with callback_query."
    try:
        return update.callback_query.from_user
    except:
        return update.message.from_user
