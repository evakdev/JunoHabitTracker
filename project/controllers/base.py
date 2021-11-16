from telegram.ext import ConversationHandler


# Base classes.
class Keys:
    def __init__(self):
        pass

class Conversation:
    def __init__(self):
        self.handler: ConversationHandler
        self.keys = Keys()
        self.add_keys()

    def add_keys(self):
        keys = Keys()
        keys.id = ""
        keys.end = -1
        keys.cancel = keys.id + "cancel"
        self.keys = keys

    def cancel(self, update, context):
        update.callback_query.edit_message_text("Canceling Command.")