import telegram
import telegram.ext
import config
import utils
from . import db
from channel import EFBChannel, EFBMsg, MsgType, MsgSource, TargetType, ChannelType


class UserStates:
    # Chat linking
    CONFIRM_LINK = 0x11
    pass


class TelegramChannel(EFBChannel):
    """
    EFB Channel - Telegram (Master)
    Requires python-telegram-bot

    Author: Eana Hufwe <https://github.com/blueset>

    Additional configs:
    eh_telegram_master = {"token": "123456789:1A2b3C4D5e6F7G8H9i0J1k2L3m4N5o6P7q8"}
    """

    # Meta Info
    channel_name = "Telegram Master"
    channel_emoji = "✈"
    channel_id = "eh_telegram_master"
    channel_type = ChannelType.Master

    # Data
    slaves = None
    bot = None
    msg_status = {}

    def __init__(self, queue, slaves):
        super().__init__(queue)
        self.slaves = slaves
        try:
            self.bot = telegram.ext.Updater(config.eh_telegram_master['token'])
        except (AttributeError, KeyError):
            raise NameError("Token is not properly defined. Please define it in `config.py`.")

        self.bot.dispatcher.add_handler(telegram.ext.CommandHandler("link", self.link_chat_show_list))
        self.bot.dispatcher.add_handler(telegram.ext.CallbackQueryHandler(self.callback_query_dispatcher))

    def callback_query_dispatcher(self, bot, update):
        query = update.callback_query
        chat_id = query.message.chat_id
        user_id = query.from_user.id
        text = query.data
        msg_id = update.inline_message_id
        msg_status = self.msg_status[msg_id]
        if msg_status in [UserStates.CONFIRM_LINK]:
            return self.link_chat_confirm_list(
                    
                )
        else:
            bot.editMessageText(text="Session expired. Please try again.",
                                chat_id=chat_id,
                                message_id=message_id)
        pass

    def process_msg(self, msg):
        pass

    def link_chat_show_list(self, bot, update):
        user_id = update.message.from_user.id
        # if update.chat_id != bot.me.id:
        #   init msg = bot.send("processing")
        #   cid = db.get_chat_assoc(master_cid=update.chat_id).slave_cid
        #   return self.link_chat_confirm_list(msg_id, msg_id=init_msg.id, chat_id=cid)
        #
        # if update.reply to:
        #   init msg = bot.send("processing")
        #   cid = db.get_chat_log(replyto.id).chat_id
        #   retrun self.link_chat_confirm_list(msg_id, msg_id=init_msg.id, chat_id=cid)
        legend = [
            "%s: Linked" % utils.Emojis.LINK_EMOJI,
            "%s: User" % utils.Emojis.USER_EMOJI,
            "%s: Group" % utils.Emojis.GROUP_EMOJI,
            "%s: System" % utils.Emojis.SYSTEM_EMOJI,
            "%s: Unknown" % utils.Emojis.UNKNOWN_EMOJI
        ]
        chat_btn_list = []
        for slave in self.slaves:
            slave_chats = slave.get_chats()
            slave_id = slave.channel_id
            slave_name = slave.channel_name
            slave_emoji = slave.channel_emoji
            legend.append("%s: %s" % (slave_emoji, slave_name))
            for chat in slave_chats:
                uid = "%s.%s" % (slave_id, chat['uid'])
                linked = utils.Emojis.LINK_EMOJI if bool(db.get_chat_assoc(slave_id=uid)) else ""
                chat_type = utils.Emojis.get_type_emoji(chat['type'])
                chat_name = chat['alias'] if chat['name'] == chat['alias'] else "%s(%s)" % (chat['alias'], chat['name'])
                chat_btn_list.append(
                    [telegram.InlineKeyboardButton(
                        "%s%s: %s%s" % (slave_emoji, chat_type, chat_name, linked), callback_data=uid)])
        msg_text = "Please choose the chat you want to link with ...\n\nLegend:\n"
        for i in legend:
            msg_text += "%s\n" % i
        msg = bot.sendMessage(user_id, text=msg_text, reply_markup=telegram.InlineKeyboardMarkup(chat_btn_list))
        self.msg_status[msg.message_id] = UserStates.CONFIRM_LINK

    def poll(self):
        self.bot.start_polling(network_delay=5)
        while True:
            if not self.queue.empty():
                msg = self.queue.get()
                self.process_msg(msg)
