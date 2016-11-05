import itchat
import requests
import re
import xmltodict
import logging
import os
import time
import magic
import mimetypes
from PIL import Image
from binascii import crc32
from channel import EFBChannel, EFBMsg, MsgType, MsgSource, TargetType, ChannelType
from utils import extra
from channelExceptions import EFBMessageTypeNotSupported

def incomeMsgMeta(func):
    def wcFunc(self, msg, isGroupChat=False):
        mobj = func(self, msg, isGroupChat)
        if isGroupChat:
            mobj.source = MsgSource.Group
            mobj.origin = {
                'name': msg['FromNickName'],
                'alias': msg['FromRemarkName'] or msg['FromNickName'],
                'uid': self.get_uid(NickName=msg['FromNickName'])
            }
            mobj.member = {
                'name': msg['ActualNickName'],
                'alias': msg['ActualDisplayName'] or msg['ActualNickName'],
                'uid': self.get_uid(NickName=msg['ActualNickName'])
            }
        else:
            mobj.source = MsgSource.User
            mobj.origin = {
                'name': msg['FromNickName'],
                'alias': msg['FromRemarkName'] or msg['FromNickName'],
                'uid': self.get_uid(NickName=msg['FromNickName'])
            }
        mobj.destination = {
            'name': itchat.client().storageClass.nickName,
            'alias': itchat.client().storageClass.nickName,
            'uid': self.get_uid(NickName=itchat.client().storageClass.userName)
        }
        logger = logging.getLogger("SlaveWC.%s" % __name__)
        logger.info("Slave - Wechat Incomming message:\nType: %s\nText: %s\n---\n" % (mobj.type, msg['Text']))
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
        itchat.auto_login(enableCmdQR=True, hotReload=True)
        self.logger = logging.getLogger("SlaveWC.%s" % __name__)
        self.logger.info("Inited!!!\n---")

    def get_uid(self, UserName=None, NickName=None):
        if not (UserName or NickName):
            print('No name provided.')
            return False
        if UserName:
            NickName = itchat.client().find_nickname(UserName)
        return crc32(NickName.encode("utf-8"))

    def get_UserName(self, uid, refresh=False):
        if refresh or len(self.users) < 1:
            usersdata = itchat.get_contract(True) + itchat.get_chatrooms()
            for i in usersdata:
                self.users[crc32(i['NickName'].encode("utf-8"))] = i['UserName']
        return self.users.get(int(uid), False)

    def poll(self):
        self.usersdata = itchat.get_contract(True) + itchat.get_chatrooms()
        @itchat.msg_register(['Text'])
        def wcText(msg):
            self.textMsg(msg)

        @itchat.msg_register(['Text'], isGroupChat=True)
        def wcTextGroup(msg):
            self.logger.info("text Msg from group %s", msg['Text'])
            self.textMsg(msg, True)

        @itchat.msg_register(['Link'])
        def wcLink(msg):
            self.linkMsg(msg)

        @itchat.msg_register(['Link'], isGroupChat=True)
        def wcLinkGroup(msg):
            self.linkMsg(msg, True)

        @itchat.msg_register(['Sticker'])
        def wcSticker(msg):
            self.stickerMsg(msg)

        @itchat.msg_register(['Sticker'], isGroupChat=True)
        def wcStickerGroup(msg):
            self.stickerMsg(msg, True)

        @itchat.msg_register(['Picture'])
        def wcPicture(msg):
            self.pictureMsg(msg)

        @itchat.msg_register(['Picture'], isGroupChat=True)
        def wcPictureGroup(msg):
            self.pictureMsg(msg, True)

        @itchat.msg_register(['Attachment'])
        def wcFile(msg):
            self.fileMsg(msg)

        @itchat.msg_register(['Attachment'], isGroupChat=True)
        def wcFileGroup(msg):
            self.fileMsg(msg, True)

        @itchat.msg_register(['Recording'])
        def wcRecording(msg):
            self.voiceMsg(msg)

        @itchat.msg_register(['Recording'], isGroupChat=True)
        def wcRecordingGroup(msg):
            self.voiceMsg(msg, True)

        @itchat.msg_register(['Map'])
        def wcLocation(msg):
            self.locationMsg(msg)

        @itchat.msg_register(['Map'], isGroupChat=True)
        def wcLocationGroup(msg):
            self.locationMsg(msg, True)

        @itchat.msg_register(['Video'])
        def wcVideo(msg):
            self.videoMsg(msg)

        @itchat.msg_register(['Video'], isGroupChat=True)
        def wcVideoGroup(msg):
            self.videoMsg(msg, True)

        itchat.run()
        while True:
            if not itchat.client().status:
                msg = EFBMsg(self)
                msg.type = MsgType.Text
                msg.source = MsgType.System
                msg.origin = {
                    "name": "EFB System",
                    "alias": "EFB System",
                    "uid": None
                }
                mobj.destination = {
                    'name': itchat.client().storageClass.nickName,
                    'alias': itchat.client().storageClass.nickName,
                    'uid': self.get_uid(NickName=itchat.client().storageClass.userName)
                }
                msg.text = "Logged out unexpectedly."

    @incomeMsgMeta
    def textMsg(self, msg, isGroupChat=False):
        self.logger.info("TextMsg!!!\n---")
        if msg['Text'].startswith("http://weixin.qq.com/cgi-bin/redirectforward?args="):
            return self.locationMsg(msg, isGroupChat)
        mobj = EFBMsg(self)
        mobj.text = msg['Text']
        mobj.type = MsgType.Text
        return mobj

    @incomeMsgMeta
    def locationMsg(self, msg, isGroupChat):
        mobj = EFBMsg(self)
        mobj.text = msg['Text']
        loc = re.search("=-?([0-9.]+),-?([0-9.]+)", requests.get(msg['text'].strip()).text).groups()
        mobj.attributes = {"longitude": float(loc[0]), "latitude": float(loc[1])}
        mobj.type = MsgType.Location
        return mobj

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
            "image": None,
            "url": data['msg']['appmsg']['url']
        }
        # format text
        mobj.text = "🔗 %s\n%s\n\n%s" % (mobj.attributes['title'], mobj.attributes['description'], mobj.attributes['url'])
        mobj.type = MsgType.Link
        return mobj

    @incomeMsgMeta
    def stickerMsg(self, msg, isGroupChat=False):
        mobj = EFBMsg(self)
        mobj.type = MsgType.Sticker
        mobj.path, mime = self.save_file(msg, mobj.type)
        mobj.text = None
        mobj.file = open(mobj.path, "rb")
        mobj.mime = mime
        return mobj

    @incomeMsgMeta
    def pictureMsg(self, msg, isGroupChat=False):
        mobj = EFBMsg(self)
        mobj.type = MsgType.Image
        mobj.path, mime = self.save_file(msg, mobj.type)
        mobj.text = None
        mobj.file = open(mobj.path, "rb")
        mobj.mime = mime
        return mobj

    @incomeMsgMeta
    def fileMsg(self, msg, isGroupChat=False):
        mobj = EFBMsg(self)
        mobj.type = MsgType.File
        mobj.path, mobj.mime = self.save_file(msg, mobj.type)
        mobj.text = msg['FileName']
        mobj.file = open(mobj.path, "rb")
        return mobj

    @incomeMsgMeta
    def voiceMsg(self, msg, isGroupChat=False):
        mobj = EFBMsg(self)
        mobj.type = MsgType.Audio
        mobj.path, mobj.mime = self.save_file(msg, mobj.type)
        mobj.text = None
        mobj.file = open(mobj.path, "rb")
        return mobj

    @incomeMsgMeta
    def videoMsg(self, msg, isGroupChat=False):
        mobj = EFBMsg(self)
        mobj.path, mobj.mime = self.save_file(msg, MsgType.Video)
        mobj.type = MsgType.Video
        mobj.text = None
        mobj.file = open(mobj.path, "rb")
        return mobj

    def save_file(self, msg, msg_type):
        path = os.path.join("storage", self.channel_id)
        if not os.path.exists(path):
            os.makedirs(path)
        filename = "%s_%s_%s" % (msg_type, msg['NewMsgId'], int(time.time()))
        fullpath = os.path.join(path, filename)
        msg['Text'](fullpath)
        mime = magic.from_file(fullpath, mime=True).decode()
        ext = mimetypes.guess_extension(mime)
        os.rename(fullpath, "%s.%s" % (fullpath, ext))
        fullpath = "%s.%s" % (fullpath, ext)
        self.logger.info("File saved from WeChat\nFull path: %s\nMIME: %s", fullpath, mime)
        return (fullpath, mime)

    def send_message(self, msg):
        """Send a message to WeChat.
        Supports text, image, sticker, and file.

        Args:
            msg (channel.EFBMsg): Message Object to be sent.

        Returns:
            This method returns nothing.

        Raises:
            EFBMessageTypeNotSupported: Raised when message type is not supported by the channel.
        """
        self.logger.info('msg.text %s', msg.text)
        UserName = self.get_UserName(msg.destination['uid'])
        self.logger.info("Sending message to Wechat:\nTarget-------\nuid: %s\nUserName: %s\nNickName: %s" % (msg.destination['uid'], UserName, itchat.find_nickname(UserName)))
        self.logger.info("Got message of type %s", msg.type)
        if msg.type == MsgType.Text:
            if msg.target:
                if msg.target['type'] == TargetType.Member:
                    msg.text = "@%s\u2005 %s" % (msg.target['target'].member['alias'], msg.text)
                elif msg.target['type'] == TargetType.Message:
                    msg.text = "@%s\u2005 「%s」\n\n%s" % (msg.target['target'].member['alias'], msg.target['target'].text, msg.text)
            r = itchat.send(msg.text, UserName)
            return r
        elif msg.type in [MsgType.Image, MsgType.Sticker]:
            self.logger.info("Image/Sticker %s", msg.type)
            if msg.mime == "image/gif":
                r = itchat.send_file(msg.path, UserName, isGIF=True)
                os.remove(msg.path)
                return r
            elif not msg.mime == "image/jpeg":  # Convert Image format
                img = Image.open(msg.path)
                bg = Image.new("RGB", img.size, (255, 255, 255))
                bg.paste(img, img)
                bg.save("%s.jpg" % msg.path)
                msg.path = "%s.jpg" % msg.path
                self.logger.info('Image converted to JPEG: %s', msg.path)
            self.logger.info('Sending Image...')
            r = itchat.send_image(msg.path, UserName)
            self.logger.info('Image sent with result %s', r)
            os.remove(msg.path)
            if not msg.mime == "image/jpeg":
                os.remove(msg.path[:-4])
            return r
        elif msg.type == MsgType.File:
            self.logger.info("Sending file to WeChat\nFileName: %s\nPath: %s", msg.text, msg.path)
            r = itchat.send_file(msg.path, UserName, filename=msg.text)
            os.remove(msg.path)
            return r
        else:
            raise EFBMessageTypeNotSupported()

    @extra(name="Refresh Contacts and Groups list", desc="Refresh the list of contacts when unidentified contacts found.", emoji="🔁")
    def refresh_contacts(self):
        itchat.get_contract(true)

    def get_chats(self, group=True, user=True):
        r = []
        if user:
            t = itchat.get_contract(True)
            for i in t:
                r.append({
                    'channel_name': self.channel_name,
                    'channel_id': self.channel_id,
                    'name': i['NickName'],
                    'alias': i['RemarkName'] or i['NickName'],
                    'uid': self.get_uid(UserName=i['UserName']),
                    'type': "User"
                })
        if group:
            t = itchat.get_chatrooms(True)
            for i in t:
                r.append({
                    'channel_name': self.channel_name,
                    'channel_id': self.channel_id,
                    'name': i['NickName'],
                    'alias': i['RemarkName'] or i['NickName'],
                    'uid': self.get_uid(UserName=i['UserName']),
                    'type': "Group"
                })
        return r

    def get_itchat(self):
        return itchat
