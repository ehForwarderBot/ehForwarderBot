import os
import inspect
from peewee import *

basePath = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))

db = SqliteDatabase(basePath + '/tgdata.db')


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


def remove_chat_assoc(master_uid=None, slave=None):
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


def add_msg_log(**kwargs):
    master_msg_id = kwargs.get('master_msg_id')
    text = kwargs.get('text')
    slave_origin_uid = kwargs.get('slave_origin_uid')
    msg_type = kwargs.get('msg_type')
    sent_to = kwargs.get('sent_to')
    slave_origin_display_name = kwargs.get('slave_origin_display_name', None)
    slave_member_uid = kwargs.get('slave_member_uid', None)
    slave_member_display_name = kwargs.get('slave_member_display_name', None)

    return MsgLog.create(master_msg_id=master_msg_id,
                         text=text,
                         slave_origin_uid=slave_origin_uid,
                         msg_type=msg_type,
                         sent_to=sent_to,
                         slave_origin_display_name=slave_origin_display_name,
                         slave_member_uid=slave_member_uid,
                         slave_member_display_name=slave_member_display_name)


def get_msg_log(master_msg_id):
    try:
        return MsgLog.get(master_msg_id=master_msg_id)
    except DoesNotExist:
        return None

db.connect()
if not ChatAssoc.table_exists():
    _create()
