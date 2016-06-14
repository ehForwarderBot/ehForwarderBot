import os
import inspect
import logging
from peewee import *

basePath = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))

db = SqliteDatabase(basePath + '/tgdata.db')
logger = logging.getLogger("masterTG.db.%s" % __name__)

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


def _create():
    db.create_tables([ChatAssoc, MsgLog])


def add_chat_assoc(master_uid, slave_uid):
    return ChatAssoc.create(master_uid=master_uid, slave_uid=slave_uid)


def remove_chat_assoc(master_uid=None, slave_uid=None):
    try:
        if bool(master_uid) == bool(slave_uid):
            raise ValueError("Only one parameter is to be provided.")
        elif master_uid:
            return ChatAssoc.get(ChatAssoc.master_uid == master_uid).delete_instance()
        elif slave_uid:
            return ChatAssoc.get(ChatAssoc.slave_uid == slave_uid).delete_instance()
    except DoesNotExist:
        return True


def get_chat_assoc(master_uid=None, slave_uid=None):
    try:
        if bool(master_uid) == bool(slave_uid):
            raise ValueError("Only one parameter is to be provided.")
        elif master_uid:
            return ChatAssoc.get(ChatAssoc.master_uid == master_uid).slave_uid
        elif slave_uid:
            return ChatAssoc.get(ChatAssoc.slave_uid == slave_uid).master_uid
    except DoesNotExist:
        return None

def get_last_msg_from_chat(chat_id):
    """Get last message from a certain chat in Telegram

    Args:
        chat_id (int/str): Chat ID

    Returns:
        Record: The last message from the chat
    """
    try:
        return MsgLog.select().where(MsgLog.master_msg_id.startswith("%s." % chat_id)).first()
        return MsgLog.select().where(MsgLog.master_msg_id.startswith("%s." % chat_id)).order_by(MsgLog.id.desc()).first()
    except DoesNotExist:
        return None


def add_msg_log(**kwargs):
    """
    master_msg_id
    text
    slave_origin_uid
    msg_type
    sent_to
    slave_origin_display_name
    slave_member_uid
    slave_member_display_name
    """
    master_msg_id = kwargs.get('master_msg_id')
    text = kwargs.get('text')
    slave_origin_uid = kwargs.get('slave_origin_uid')
    msg_type = kwargs.get('msg_type')
    sent_to = kwargs.get('sent_to')
    slave_origin_display_name = kwargs.get('slave_origin_display_name', None)
    slave_member_uid = kwargs.get('slave_member_uid', None)
    slave_member_display_name = kwargs.get('slave_member_display_name', None)
    msg_id = kwargs.get('ID', None)
    if msg_id:
        msg_log = MsgLog.get(MsgLog.id == msg_id)
        msg_log.text = text
        msg_log.master_msg_id = master_msg_id
        msg_log.text = text
        msg_log.msg_type = msg_type
        msg_log.sent_to = sent_to
        msg_log.slave_origin_uid = slave_origin_uid
        msg_log.slave_origin_display_name = slave_origin_display_name
        msg_log.slave_member_uid = slave_member_uid
        msg_log.slave_member_display_name = slave_member_display_name
        msg_log.save()
        return msg_log
    else:
        return MsgLog.create(master_msg_id=master_msg_id,
                             text=text,
                             slave_origin_uid=slave_origin_uid,
                             msg_type=msg_type,
                             sent_to=sent_to,
                             slave_origin_display_name=slave_origin_display_name,
                             slave_member_uid=slave_member_uid,
                             slave_member_display_name=slave_member_display_name)


def get_msg_log(master_msg_id):
    logger.info("get_msg_log %s" % master_msg_id)
    try:
        return MsgLog.select().where(MsgLog.master_msg_id == master_msg_id).first()
        return MsgLog.select().where(MsgLog.master_msg_id == master_msg_id).order_by(MsgLog.id.desc()).first()
    except DoesNotExist:
        return None

db.connect()
if not ChatAssoc.table_exists():
    _create()
