from . import itchat
import requests
import re
import xmltodict
from binascii import crc32
from channel import EFBChannel, EFBMsg, MsgType, MsgSource, TargetType, ChannelType
from utils import extra

def incomeMsgMeta(func):
    def wcFunc(self, msg, isGroupChat=False):
        mobj = self.func(msg, isGroupChat)
        if isGroupChat:
            mobj.source = MsgSource.Group
            mobj.origin = {
                'name': msg['FromNickName'],
                'alias': msg['FromRemarkName'] or msg['FromNickName'],
                'uid': self.get_uid(msg['FromUserName'])
            }
            mobj.member = {
                'name': msg['ActualNickName'],
                'alias': msg['ActualDisplayName'],
                'uid': self.get_uid(msg['ActualUserName'])
            }
        else:
            mobj.source = MsgSource.User
            mobj.origin = {
                'name': msg['FromNickName'],
                'alias': msg['FromRemarkName'] or msg['FromNickName'],
                'uid': self.get_uid(msg['FromUserName'])
            }
        mobj.destination = {
            'name': itchat.__client.storageClass.nickName,
            'alias': itchat.__client.storageClass.nickName,
            'uid': self.get_uid(itchat.__client.storageClass.userName)
        }
        self.queue.put(mobj)
    return wcFunc


class WeChatChannel(EFBChannel):
    """
    EFB Channel - WeChat (slave)
    Based on itchat (modified by Eana Hufwe)

    Author: Eana Hufwe <https://github.com/blueset>
    """
    channel_name = "WeChat Slave"
    channel_emoji = "💬"
    channel_id = "eh_wechat_slave"
    channel_type = ChannelType.Slave
    users = {}

    def __init__(self, queue):
        super().__init__(queue)
        #itchat.auto_login()
        #usersdata = itchat.get_contract(True) + itchat.get_chatrooms()

    def get_uid(self, UserName=None, NickName=None):
        if not (UserName or NickName):
            print('No name provided.')
            return False
        if UserName:
            NickName = itchat.__client.storageClass.find_nickname(UserName)
        return crc32(NickName)

    def get_UserName(self, uid, refresh=False):
        if refresh or len(self.users) < 1:
            usersdata = itchat.get_contract(True) + itchat.get_chatrooms()
            for i in usersdata:
                self.users[crc32(i['NickName'])] = i['UserName']
        return self.users.get(uid, False)

    def poll(self):
        @itchat.msg_register(['Text'])
        def wcText(msg):
            self.textMsg(msg)

        @itchat.msg_register(['Text'], isGroupChat=True)
        def wcTextGroup(msg):
            self.textMsg(msg, True)

        @itchat.msg_register(['Link'])
        def wcLink(msg):
            self.linkMsg(msg)

        @itchat.msg_register(['Link'], isGroupChat=True)
        def wcLinkGroup(msg):
            self.linkMsg(msg, True)

        itchat.start_receiving()

    @incomeMsgMeta
    def textMsg(self, msg, isGroupChat=False):
        if msg['Text'].startswith("http://weixin.qq.com/cgi-bin/redirectforward?args="):
            return self.locationMsg(msg, isGroupChat)
        mobj = EFBMsg(self)
        mobj.text = msg['Text']
        mobj.type = MsgType.Text

    @incomeMsgMeta
    def locationMsg(self, msg, isGroupChat):
        mobj = EFBMsg(self)
        mobj.text = msg['Text']
        loc = re.search("center=([0-9.]+),([0-9.]+)", requests.get(msg['text'].strip()).text).groups()
        mobj.attributes = {"longitude": loc[0], "latitude": loc[1]}
        mobj.type = MsgType.Location

    @incomeMsgMeta
    def linkMsg(self, msg, isGroupChat=False):
        # initiate object
        mobj = EFBMsg(self)
        # parse XML
        xmldata = itchat.tools.escape_emoji(msg['Meta'])
        data = xmltodict.parse(xmldata)
        # set attributes
        mobj.attributes = {
            "title": data['msg']['appmsg']['title'],
            "description": data['msg']['appmsg']['des'],
            "url": data['msg']['appmsg']['url']
        }
        # format text
        mobj.text = "🔗 %s\n%s\n\n%s" % (mobj.attributes['title'], mobj.attributes['description'], mobj.attributes['url'])
        mobj.type = MsgType.Link

    def send_message(self, msg):
        UserName = self.get_UserName(msg['destination']['uid'])
        if msg.type == MsgType.Text:
            if msg.target:
                if msg.target['type'] == TargetType.Member:
                    msg.text = "@%s\u2005 %s" % (msg.target['target']['alias'], msg.text)
                elif msg.target['type'] == TargetType.Message:
                    msg.text = "@%s\u2005 「%s」\n\n%s" % (msg.target['target'].member['alias'], msg.target['target'].text, msg.text)
            itchat.send(msg.text, UserName)

    @extra(name="Refresh Contacts and Groups list", desc="Refresh the list of contacts when unidentified contacts found.", emoji="🔁")
    def refresh_contacts(self):
        itchat.get_contract(True)

    def get_chats(self, group=True, user=True):
        r = []
        if user:
            t = itchat.get_contract(True)
            for i in t:
                r.append({
                    'channel_name': self.channel_name,
                    'name': i['NickName'],
                    'alias': i['RemarkName'] or i['NickName'],
                    'uid': self.get_uid(i['UserName']),
                    'type': "User"
                })
        if group:
            t = itchat.get_contract(True)
            for i in t:
                r.append({
                    'channel_name': self.channel_name,
                    'channel_id': self.channel_id,
                    'name': i['NickName'],
                    'alias': i['RemarkName'] or i['NickName'],
                    'uid': self.get_uid(i['UserName']),
                    'type': "Group"
                })
        return r
