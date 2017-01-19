import os
import inspect
import logging
import datetime
from peewee import *
from playhouse.migrate import *

basePath = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))

db = SqliteDatabase(basePath + '/tgdata.db')
logger = logging.getLogger("plugins.eh_telegram_master.db")

# Peewee Models

class BaseModel(Model):

    class Meta:
        database = db


class ChatAssoc(BaseModel):
    master_uid = CharField()
    slave_uid = CharField()


class MsgLog(BaseModel):
    master_msg_id = CharField(unique=True, primary_key=True)
    text = CharField()
    slave_origin_uid = CharField()
    slave_origin_display_name = CharField(null=True)
    slave_member_uid = CharField(null=True)
    slave_member_display_name = CharField(null=True)
    msg_type = CharField()
    sent_to = CharField()
    time = DateTimeField(default=datetime.datetime.now, null=True)


def _create():
    """
    Initializing tables.
    """
    db.create_tables([ChatAssoc, MsgLog])


def _migrate(i):
    """
    Run migrations.

    Args:
        i: Migration ID

    Returns:
        False: when migration ID is not found
    """
    if i == 0:
        # Migrate 0: Added Time column in MsgLog table.
        # 2016JUN15
        migrator = SqliteMigrator(db)
        migrate(migrator.add_column("msglog", "time", DateTimeField(default=datetime.datetime.now, null=True)))
    else:
        return False


def add_chat_assoc(master_uid, slave_uid, multiple_slave=False):
    """
    Add chat associations (chat links).
    One Master channel with many Slave channel.

    Args:
        master_uid (str): Master channel UID ("%(chat_id)s")
        slave_uid (str): Slave channel UID ("%(channel_id)s.%(chat_id)s")
    """
    if not multiple_slave:
        remove_chat_assoc(master_uid=master_uid)
    remove_chat_assoc(slave_uid=slave_uid)
    return ChatAssoc.create(master_uid=master_uid, slave_uid=slave_uid)


def remove_chat_assoc(master_uid=None, slave_uid=None):
    """
    Remove chat associations (chat links).
    Only one parameter is to be provided.

    Args:
        master_uid (str): Master channel UID ("%(chat_id)s")
        slave_uid (str): Slave channel UID ("%(channel_id)s.%(chat_id)s")
    """
    try:
        if bool(master_uid) == bool(slave_uid):
            raise ValueError("Only one parameter is to be provided.")
        elif master_uid:
            return ChatAssoc.delete().where(ChatAssoc.master_uid == master_uid).execute()
        elif slave_uid:
            return ChatAssoc.delete().where(ChatAssoc.slave_uid == slave_uid).execute()
    except DoesNotExist:
        return 0


def get_chat_assoc(master_uid=None, slave_uid=None):
    """
    Get chat association (chat link) information.
    Only one parameter is to be provided.

    Args:
        master_uid (str): Master channel UID ("%(chat_id)s")
        slave_uid (str): Slave channel UID ("%(channel_id)s.%(chat_id)s")

    Returns:
        list: The counterpart ID.
    """
    try:
        if bool(master_uid) == bool(slave_uid):
            raise ValueError("Only one parameter is to be provided.")
        elif master_uid:
            slaves = ChatAssoc.select().where(ChatAssoc.master_uid == master_uid)
            if len(slaves) > 0:
                return [i.slave_uid for i in slaves]
            else:
                return []
        elif slave_uid:
            masters = ChatAssoc.select().where(ChatAssoc.slave_uid == slave_uid)
            if len(masters) > 0:
                return [i.master_uid for i in masters]
            else:
                return []
    except DoesNotExist:
        return []


def get_last_msg_from_chat(chat_id):
    """Get last message from the selected chat from Telegram

    Args:
        chat_id (int|str): Telegram chat ID

    Returns:
        MsgLog: The last message from the chat
    """
    try:
        return MsgLog.select().where(MsgLog.master_msg_id.startswith("%s." % chat_id)).order_by(MsgLog.time.desc()).first()
    except DoesNotExist:
        return None


def add_msg_log(**kwargs):
    """
    Add an entry to message log.

    Display name is defined as `alias or name`.

    Args:
        master_msg_id (str): Telegram message ID ("%(chat_id)s.%(msg_id)s")
        text (str): String representation of the message
        slave_origin_uid (str): Slave chat ID ("%(channel_id)s.%(chat_id)s")
        msg_type (str): String of the message type.
        sent_to (str): "master" or "slave"
        slave_origin_display_name (str): Display name of slave chat.
        slave_member_uid (str|None):
            User ID of the slave chat member (sender of the message, for group chat only).
            ("%(channel_id)s.%(chat_id)s"), None if not available.
        slave_member_display_name (str|None):
            Display name of the member, None if not available.
        update (bool): Update a previous record. Default: False.

    Returns:
        MsgLog: The added/updated entry.
    """
    master_msg_id = kwargs.get('master_msg_id')
    text = kwargs.get('text')
    slave_origin_uid = kwargs.get('slave_origin_uid')
    msg_type = kwargs.get('msg_type')
    sent_to = kwargs.get('sent_to')
    slave_origin_display_name = kwargs.get('slave_origin_display_name', None)
    slave_member_uid = kwargs.get('slave_member_uid', None)
    slave_member_display_name = kwargs.get('slave_member_display_name', None)
    slave_message_uid = kwargs.get('slave_message_uid', None)
    update = kwargs.get('update', False)
    if update:
        msg_log = MsgLog.get(MsgLog.master_msg_id == master_msg_id)
        msg_log.text = text
        msg_log.msg_type = msg_type
        msg_log.sent_to = sent_to
        msg_log.slave_origin_uid = slave_origin_uid
        msg_log.slave_origin_display_name = slave_origin_display_name
        msg_log.slave_member_uid = slave_member_uid
        msg_log.slave_member_display_name = slave_member_display_name
        # msg_log.slave_message_uid = slave_message_uid
        msg_log.save()
        return msg_log
    else:
        return MsgLog.create(master_msg_id=master_msg_id,
                             # slave_message_uid=slave_message_uid
                             text=text,
                             slave_origin_uid=slave_origin_uid,
                             msg_type=msg_type,
                             sent_to=sent_to,
                             slave_origin_display_name=slave_origin_display_name,
                             slave_member_uid=slave_member_uid,
                             slave_member_display_name=slave_member_display_name)


def get_msg_log(master_msg_id):
    """Get message log by message ID.

    Args:
        master_msg_id (str): Telegram message ID ("%(chat_id)s.%(msg_id)s")

    Returns:
        MsgLog|None: The queried entry, None if not exist.
    """
    logger.info("get_msg_log %s" % master_msg_id)
    try:
        return MsgLog.select().where(MsgLog.master_msg_id == master_msg_id).order_by(MsgLog.time.desc()).first()
    except DoesNotExist:
        return None

db.connect()
if not ChatAssoc.table_exists():
    _create()
elif "time" not in [i.name for i in db.get_columns("msglog")]:
    _migrate(0)
