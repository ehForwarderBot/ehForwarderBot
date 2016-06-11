from telegram.ext.handler import Handler
from telegram import Update
from telegram.utils.deprecate import deprecate


class WhitelistHandler(Handler):
    """
    Handler class to block users not on white-list.

    Args:
        whitelist (list[int]): A list consist of whitelisted user IDs
            in int.
        pass_update_queue (optional[bool]): If the handler should be passed the
            update queue as a keyword argument called ``update_queue``. It can
            be used to insert updates. Default is ``False``
    """

    def __init__(self, whitelist, pass_update_queue=False):
        def void_function(bot, update):
            pass

        self.whitelist = list(map(lambda i: int(i), whitelist))
        super(WhitelistHandler, self).__init__(void_function, pass_update_queue)

    def check_update(self, update):
        if getattr(update, "message", None):
            obj = update.message
        elif getattr(update, "callback_query", None):
            obj = update.callback_query
        elif getattr(update, "edited_message", None):
            obj = update.edited_message
        return isinstance(update, Update) and not int(obj.from_user.id) in self.whitelist

    def handle_update(self, update, dispatcher):
        pass

    # old non-PEP8 Handler methods
    m = "telegram.WhitelistHandler."
    checkUpdate = deprecate(check_update, m + "checkUpdate", m + "check_update")
    handleUpdate = deprecate(handle_update, m + "handleUpdate", m + "handle_update")
