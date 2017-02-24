import io
import logging
import mimetypes
import os
import re
import threading
import time
import html
from binascii import crc32

import itchat
import magic
import xmltodict
from pyqrcode import QRCode
from PIL import Image

import config
from channel import EFBChannel, EFBMsg, MsgType, MsgSource, TargetType, ChannelType
from channelExceptions import EFBMessageTypeNotSupported, EFBMessageError, EFBChatNotFound
from utils import extra


def wechat_msg_meta(func):
    def wrap_func(self, msg, *args, **kwargs):
        isGroupChat = str(msg['FromUserName']).startswith("@@")
        logger = logging.getLogger("plugins.%s.wechat_msg_meta" % self.channel_id)
        logger.debug("Raw message: %s" % repr(msg))
        mobj = func(self, msg, *args, **kwargs)
        if mobj is None:
            return
        mobj.uid = msg.get("MsgId", time.time())
        me = msg['FromUserName'] == self.itchat.loginInfo['User']['UserName']
        logger.debug("me, %s", me)
        if me:
            msg['FromUserName'], msg['ToUserName'] = msg['ToUserName'], msg['FromUserName']
        FromUser = self.search_user(UserName=msg['FromUserName']) or \
                   self.search_user(UserName=msg['FromUserName'], refresh=True) or \
                   [{"NickName": "Chat not found. (UE01)", "RemarkName": "Chat not found. (UE01)", "Uin": 0}]
        FromUser = FromUser[0]
        logger.debug("From user, %s", FromUser)
        if isGroupChat:
            logger.debug("Group chat")
            if me:
                msg['ActualUserName'] = msg['ToUserName']
                member = {"NickName": self._wechat_html_unescape(self.itchat.loginInfo['User']['NickName']),
                          "DisplayName": "You",
                          "Uin": self.itchat.loginInfo['User']['Uin']}
            else:
                logger.debug("search_user")
                member = self.search_user(UserName=msg['FromUserName'], ActualUserName=msg['ActualUserName'])[0]['MemberList'][0]
                logger.debug("search_user.done")
            mobj.source = MsgSource.Group
            logger.debug("Group. member: %s", member)
            mobj.origin = {
                'name': html.unescape(FromUser['NickName']),
                'alias': html.unescape(FromUser['RemarkName'] or FromUser['NickName']),
                'uid': self.get_uid(UserName=msg.get('FromUserName', None),
                                    NickName=self._wechat_html_unescape(FromUser.get('NickName', "s")),
                                    alias=self._wechat_html_unescape(FromUser.get('RemarkName', "s")),
                                    Uin=FromUser.get('Uin', None))
            }
            mobj.member = {
                'name': self._wechat_html_unescape(member['NickName']),
                'alias': self._wechat_html_unescape(member['DisplayName']),
                'uid': self.get_uid(UserName=msg.get('ActualUserName', None),
                                    NickName=self._wechat_html_unescape(member.get('NickName', "")),
                                    alias=self._wechat_html_unescape(member.get('DisplayName', "")),
                                    Uin=member.get('Uin', None))
            }
            logger.debug("origin: %s\nmember: %s\n", mobj.origin, mobj.member)
        else:
            if me:
                mobj.text = mobj.text or ""
                mobj.text = "You: " + mobj.text
            mobj.source = MsgSource.User
            mobj.origin = {
                'name': self._wechat_html_unescape(FromUser['NickName']),
                'alias': self._wechat_html_unescape(FromUser['RemarkName'] or FromUser['NickName']),
                'uid': self.get_uid(UserName=msg.get('FromUserName', None),
                                    NickName=self._wechat_html_unescape(FromUser.get('NickName', "")),
                                    alias=self._wechat_html_unescape(FromUser.get('RemarkName', "")),
                                    Uin=FromUser.get('Uin', None))
            }
        mobj.destination = {
            'name': self._wechat_html_unescape(self.itchat.loginInfo['User']['NickName']),
            'alias': self._wechat_html_unescape(self.itchat.loginInfo['User']['NickName']),
            'uid': self.get_uid(UserName=msg['ToUserName'])
        }
        logger.debug("dest: %s", mobj.destination)
        logger.info("WeChat incoming message:\nType: %s\nText: %s\nUserName: %s\nuid: %s\nname: %s" %
                    (mobj.type, msg['Text'], msg['FromUserName'], mobj.origin['uid'], mobj.origin['name']))
        self.queue.put(mobj)

    return wrap_func


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

    supported_message_types = {MsgType.Text, MsgType.Sticker, MsgType.Image,
                               MsgType.File, MsgType.Video, MsgType.Link, MsgType.Audio}
    logger = logging.getLogger("plugins.%s.WeChatChannel" % channel_id)
    qr_uuid = ""
    done_reauth = threading.Event()
    _stop_polling = False

    def __init__(self, queue, mutex):
        super().__init__(queue, mutex)
        self.itchat = itchat.new_instance()
        itchat.set_logging(loggingLevel=logging.getLogger().level, showOnCmd=False)
        self.itchat_msg_register()
        with mutex:
            self.itchat.auto_login(enableCmdQR=2,
                                   hotReload=True,
                                   statusStorageDir="storage/%s.pkl" % self.channel_id,
                                   exitCallback=self.exit_callback,
                                   qrCallback=self.console_qr_code)
        mimetypes.init(files=["mimetypes"])
        self.logger.info("EWS Inited!!!\n---")

    #
    # Utilities
    #

    def console_qr_code(self, uuid, status, qrcode):
        status = int(status)
        if status == 201:
            QR = 'Tap "Confirm" to continue.'
            return self.logger.critical(QR)
        elif status == 200:
            QR = "Successfully authorized."
            return self.logger.critical(QR)
        elif uuid != self.qr_uuid:
            # 0: First QR code
            # 408: Updated QR code
            QR = "WeChat: Scan QR code with WeChat to continue. (%s, %s)\n" % (uuid, status)
            if status == 408:
                QR += "Previous code expired. Please scan the new one.\n"
            QR += "\n"
            qr_url = "https://login.weixin.qq.com/l/" + uuid
            QR += QRCode(qr_url).terminal()
            QR += "\nIf you cannot read the QR code above, " \
                  "please visit the following URL:\n" \
                  "https://login.weixin.qq.com/qrcode/" + uuid
            return self.logger.critical(QR)
        self.qr_uuid = uuid

    def master_qr_code(self, uuid, status, qrcode):
        status = int(status)
        msg = EFBMsg(self)
        msg.type = MsgType.Text
        msg.source = MsgSource.System
        msg.origin = {
            'name': '%s Auth' % self.channel_name,
            'alias': '%s Auth' % self.channel_name,
            'uid': -1
        }
        if status == 201:
            msg.type = MsgType.Text
            msg.text = 'Tap "Confirm" to continue.'
        elif status == 200:
            msg.type = MsgType.Text
            msg.text = "Successfully authenticated."
        elif uuid != self.qr_uuid:
            msg.type = MsgType.Image
            path = os.path.join("storage", self.channel_id)
            if not os.path.exists(path):
                os.makedirs(path)
            path = os.path.join(path, 'QR-%s.jpg' % int(time.time()))
            self.logger.debug("master_qr_code file path: %s", path)
            qr_url = "https://login.weixin.qq.com/l/" + uuid
            QRCode(qr_url).png(path, scale=10)
            msg.text = 'Scan this QR Code with WeChat to continue.'
            msg.path = path
            msg.file = open(path, 'rb')
            msg.mime = 'image/jpeg'
        if status in (200, 201) or uuid != self.qr_uuid:
            self.queue.put(msg)
            self.qr_uuid = uuid

    def exit_callback(self):
        if self.stop_polling:
            return
        msg = EFBMsg(self)
        msg.source = MsgSource.System
        msg.origin = {
            'name': '%s System' % self.channel_name,
            'alias': '%s System' % self.channel_name,
            'uid': -1
        }
        msg.text = "WeChat server logged out the user."
        msg.type = MsgType.Text
        on_log_out = self._flag("on_log_out", "command")
        on_log_out = on_log_out if on_log_out in ("command", "idle", "reauth") else "command"
        if on_log_out == "command":
            msg.type = MsgType.Command
            msg.attributes = {
                "commands": [
                    {
                        "name": "Log in",
                        "callable": "reauth",
                        "args": [],
                        "kwargs": {"command": True}
                    }
                ]
            }
        elif on_log_out == "reauth":
            if self._flag("qr_reload", "master_qr_code") == "console_qr_code":
                msg.text += "\nPlease visit your console or log for QR code and further instructions."
            self.reauth()

        self.queue.put(msg)

    def get_uid(self, UserName=None, NickName=None, alias=None, Uin=None):
        """
        Get unique identifier of a chat, by UserName or NickName.
        Fill in `UserName` or `NickName`.

        Args:
            UserName (str): WeChat `UserName` of the chat.
            NickName (str): Name (`NickName`) of the chat.
            alias (str): Alias ("Display Name" or "Remark Name") of the user
            Uin: WeChat Unique Identifier.

        Returns:
            str|bool: Unique ID of the chat. `False` if not found.
        """
        if UserName and not str(UserName).startswith("@"):
            return UserName
        if not (UserName or NickName or alias or Uin):
            self.logger.error('No name provided.')
            return False
        data = {"nickname": NickName, "alias": alias, "uin": Uin}
        if UserName and not (NickName or alias or Uin):
            r = self.search_user(UserName=UserName)
            if not r:
                self.logger.debug("get_uid, return False")
                return False
            data = {"nickname": r[0]['NickName'], "alias": r[0]["RemarkName"], "uin": r[0]["Uin"]}
        return self.encode_uid(data)

    def encode_uid(self, data):
        """
        Encode uid by a predefined order in configuration.

        Args:
            data (dict): a dict with keys `{"nickname", "alias", "uin"}`

        Returns:
            str: Encoded uid
        """
        fallback_order = self._flag("uid_order", ["NickName"])
        uid = data[fallback_order[-1].lower()]
        for i in fallback_order:
            if data[i.lower()]:
                uid = data[i.lower()]
                break
        return str(crc32(str(uid).encode("utf-8")))

    def get_UserName(self, uid, refresh=False):
        """
        Get WeChat `UserName` of a chat by UID.

        Args:
            uid (str): UID of the chat.
            refresh (bool): Refresh the chat list from WeChat, `False` by default.

        Returns:
            str|bool: `UserName` of the chosen chat. `False` if not found.
        """
        if uid and str(uid).isalpha():
            return uid
        r = self.search_user(uid=uid, refresh=refresh)
        if r:
            return r[0]['UserName']
        return None

    def search_user(self, UserName=None, uid=None, uin=None, name=None, ActualUserName=None, refresh=False):
        """
        Search for a WeChat "User" (a user, a group/chat room or an MP account,
        by `UserName`, unique ID, WeChat ID, name/alias, and/or group member `UserName`.

        At least one of `UserName`, `uid`, `wid`, or `name` should be provided.

        When matching for a group, all of `UserName`, `uid`, `wid`, and `name` will be used
        to match for group and member.

        Args:
            UserName (str): UserName of a "User"
            uid (str): Unique ID generated by the channel
            uin (str): WeChat Unique Identifier.
            name (str): Name or Alias
            ActualUserName (str): UserName of a group member, used only when a group is matched.
            refresh (bool): Refresh the user list, False by default.

        Returns:
            list of dict: A list of matching users in ItChat user dict format.
        """
        result = []
        UserName = None if UserName is None else str(UserName)
        uid = None if uid is None else str(uid)
        uin = None if uin is None else str(uin)
        name = None if name is None else str(name)
        ActualUserName = None if ActualUserName is None else str(ActualUserName)

        if all(i is None for i in [UserName, uid, uin, name]):
            raise ValueError("At least one of [UserName, uid, uin, name] should be provided.")

        if (UserName and not str(UserName).startswith("@")) or (uin and str(uin).isalpha()):
            sys_chat_id = UserName or uin
            return [{"UserName": sys_chat_id,
                     "NickName": "System (%s)" % sys_chat_id,
                     "RemarkName": "System (%s)" % sys_chat_id,
                     "Uin": sys_chat_id}]

        for i in self.itchat.get_friends(refresh) + self.itchat.get_mps(refresh):
            data = {"nickname": self._wechat_html_unescape(i.get('NickName', None)),
                    "alias": self._wechat_html_unescape(i.get("RemarkName", None)),
                    "uin": i.get("Uin", None)}
            if self.encode_uid(data) == uid or \
                            str(i.get('UserName', '')) == UserName or \
                            str(i.get('AttrStatus', '')) == uid or \
                            str(i.get('Uin', '')) == uin or \
                            str(i.get('NickName', '')) == name or \
                            str(i.get('DisplayName', '')) == name:
                i['NickName'] = self._wechat_html_unescape(i.get('NickName', ''))
                i['DisplayName'] = self._wechat_html_unescape(i.get('DisplayName', ''))
                result.append(i.copy())
        for i in self.itchat.get_chatrooms(refresh):
            if not i['UserName'].startswith('@@'):
                continue
            if not i.get('MemberList', ''):
                i = self.itchat.update_chatroom(i.get('UserName', ''))
            data = {"nickname": self._wechat_html_unescape(i.get('NickName', None)),
                    "alias": self._wechat_html_unescape(i.get("RemarkName", None)),
                    "uin": i.get("Uin", None)}
            if self.encode_uid(data) == uid or \
                            str(i.get('Uin', '')) == uin or \
                            str(i.get('NickName', '')) == name or \
                            str(i.get('DisplayName', '')) == name or \
                            str(i.get('UserName', '')) == UserName:
                i['NickName'] = self._wechat_html_unescape(i.get('NickName', ''))
                i['DisplayName'] = self._wechat_html_unescape(i.get('DisplayName', ''))
                result.append(i.copy())
                result[-1]['MemberList'] = []
                if ActualUserName:
                    for j in i['MemberList']:
                        if str(j['UserName']) == ActualUserName:
                            j['NickName'] = self._wechat_html_unescape(j.get('NickName', ''))
                            j['DisplayName'] = self._wechat_html_unescape(j.get('DisplayName', ''))
                            result[-1]['MemberList'].append(j)
        if not result and not refresh:
            return self.search_user(UserName, uid, uin, name, ActualUserName, refresh=True)
        return result

    def poll(self):
        while not self.stop_polling:
            if self.itchat.alive:
                self.itchat.configured_reply()
            else:
                self.done_reauth.wait()
                self.done_reauth.clear()

        if self.itchat.useHotReload:
            self.itchat.dump_login_status("storage/%s.pkl" % self.channel_id)

        self.itchat.alive = False
        self.logger.debug("%s (%s) gracefully stopped.", self.channel_name, self.channel_id)

    def itchat_msg_register(self):
        self.itchat.msg_register(['Text'], isFriendChat=True, isMpChat=True, isGroupChat=True)(self.wechat_text_msg)
        self.itchat.msg_register(['Sharing'], isFriendChat=True, isMpChat=True, isGroupChat=True)(self.wechat_link_msg)
        self.itchat.msg_register(['Picture'], isFriendChat=True, isMpChat=True, isGroupChat=True)(self.wechat_picture_msg)
        self.itchat.msg_register(['Attachment'], isFriendChat=True, isMpChat=True, isGroupChat=True)(self.wechat_file_msg)
        self.itchat.msg_register(['Recording'], isFriendChat=True, isMpChat=True, isGroupChat=True)(self.wechat_voice_msg)
        self.itchat.msg_register(['Map'], isFriendChat=True, isMpChat=True, isGroupChat=True)(self.wechat_location_msg)
        self.itchat.msg_register(['Video'], isFriendChat=True, isMpChat=True, isGroupChat=True)(self.wechat_video_msg)
        self.itchat.msg_register(['Card'], isFriendChat=True, isMpChat=True, isGroupChat=True)(self.wechat_card_msg)
        self.itchat.msg_register(['Friends'], isFriendChat=True, isMpChat=True, isGroupChat=True)(self.wechat_friend_msg)
        self.itchat.msg_register(['Useless', 'Note'], isFriendChat=True, isMpChat=True, isGroupChat=True)(self.wechat_system_msg)

        @self.itchat.msg_register(["System"], isFriendChat=True, isMpChat=True, isGroupChat=True)
        def wc_msg_system_log(msg):
            self.logger.debug("WeChat \"System\" message:\n%s", repr(msg))

    @wechat_msg_meta
    def wechat_text_msg(self, msg):
        if msg['FromUserName'] == "newsapp" and msg['Content'].startswith("<mmreader>"):
            self.wechat_newsapp_msg(msg)
            return
        if msg['Text'].startswith("http://weixin.qq.com/cgi-bin/redirectforward?args="):
            self.wechat_location_msg(msg)
            return
        mobj = EFBMsg(self)
        mobj.text = msg['Text']
        mobj.type = MsgType.Text
        return mobj

    @wechat_msg_meta
    def wechat_system_msg(self, msg):
        mobj = EFBMsg(self)
        mobj.text = "System message: %s" % msg['Text']
        mobj.type = MsgType.Text
        return mobj

    @wechat_msg_meta
    def wechat_location_msg(self, msg):
        mobj = EFBMsg(self)
        mobj.text = msg['Content'].split('\n')[0][:-1]
        loc = re.search("=-?([0-9.]+),-?([0-9.]+)", msg['Url']).groups()
        mobj.attributes = {"longitude": float(loc[1]), "latitude": float(loc[0])}
        mobj.type = MsgType.Location
        return mobj

    @wechat_msg_meta
    def wechat_link_msg(self, msg):
        # self.logger.info("---\nNew Link msg, %s", msg)
        # # initiate object
        # mobj = EFBMsg(self)
        # parse XML
        itchat.utils.emoji_formatter(msg, 'Content')
        xml_data = msg['Content']
        data = xmltodict.parse(xml_data)
        # # set attributes
        base_data = [
            data.get('msg', {}).get('appmsg', {}).get('title', None),
            data.get('msg', {}).get('appmsg', {}).get('des', None),
            data.get('msg', {}).get('appmsg', {}).get('thumburl', None),
            data.get('msg', {}).get('appmsg', {}).get('url', None)
        ]
        # if mobj.attributes['url'] is None:
        #     txt = mobj.attributes['title'] or ''
        #     txt += mobj.attributes['description'] or ''
        #     msg['Text'] = txt
        #     return self.wechat_text_msg(msg)
        # format text
        # mobj.text = ""
        extra_link = data.get('msg', {}).get('appmsg', {}).get('mmreader', {}).get('category', {}).get('item', [])
        if not isinstance(extra_link, list):
            extra_link = [extra_link]
        if self._flag("first_link_only", False):
            extra_link = extra_link[:1]
        for i in extra_link:
            self.wechat_raw_link_msg(msg, i['title'], i['digest'], i['cover'], i['url'])
        if not extra_link:
            self.wechat_raw_link_msg(msg, *base_data)
        return

    @wechat_msg_meta
    def wechat_raw_link_msg(self, msg, title, description, image, url):
        mobj = EFBMsg(self)
        if url:
            mobj.type = MsgType.Link
            mobj.attributes = {
                "title": title,
                "description": description,
                "image": image,
                "url": url
            }
        else:
            mobj.type = MsgType.Text
            mobj.text = "%s\n%s" % (title, description)
            if image:
                mobj.text += "\n\n%s" % image
        return mobj

    def wechat_newsapp_msg(self, msg):
        data = xmltodict.parse(msg['Content'])
        news = data.get('mmreader', {}).get('category', {}).get('newitem', [])
        if news:
            self.wechat_raw_link_msg(msg, news[0]['title'], news[0]['digest'], news[0]['cover'], news[0]['shorturl'])
            if self._flag("extra_links_on_message", False):
                for i in news[1:]:
                    self.wechat_raw_link_msg(msg, i['title'], i['digest'], i['cover'], i['shorturl'])

    @wechat_msg_meta
    def wechat_picture_msg(self, msg):
        mobj = EFBMsg(self)
        mobj.type = MsgType.Image if msg['MsgType'] == 3 else MsgType.Sticker
        mobj.path, mime = self.save_file(msg, mobj.type)
        mobj.text = None
        mobj.file = open(mobj.path, "rb")
        mobj.mime = mime
        return mobj

    @wechat_msg_meta
    def wechat_file_msg(self, msg):
        mobj = EFBMsg(self)
        mobj.type = MsgType.File
        mobj.path, mobj.mime = self.save_file(msg, mobj.type)
        mobj.text = msg['FileName']
        mobj.filename = msg['FileName'] or None
        mobj.file = open(mobj.path, "rb")
        return mobj

    @wechat_msg_meta
    def wechat_voice_msg(self, msg):
        mobj = EFBMsg(self)
        mobj.type = MsgType.Audio
        mobj.path, mobj.mime = self.save_file(msg, mobj.type)
        mobj.text = None
        mobj.file = open(mobj.path, "rb")
        return mobj

    @wechat_msg_meta
    def wechat_video_msg(self, msg):
        mobj = EFBMsg(self)
        mobj.path, mobj.mime = self.save_file(msg, MsgType.Video)
        mobj.type = MsgType.Video
        mobj.text = None
        mobj.file = open(mobj.path, "rb")
        return mobj

    @wechat_msg_meta
    def wechat_card_msg(self, msg):
        mobj = EFBMsg(self)
        txt = ("Name card: {NickName}\n"
               "From: {Province}, {City}\n"
               "QQ: {QQNum}\n"
               "ID: {Alias}\n"
               "Signature: {Signature}\n"
               "Gender: {Sex}")
        txt = txt.format(**msg['Text'])
        mobj.text = txt
        mobj.type = MsgType.Command
        mobj.attributes = {
            "commands": [
                {
                    "name": "Send friend request",
                    "callable": "add_friend",
                    "args": [],
                    "kwargs": {
                        "userName": msg['Text']['UserName'],
                        "status": 2,
                        "ticket": ""
                    }
                }
            ]
        }
        return mobj

    @wechat_msg_meta
    def wechat_friend_msg(self, msg):
        mobj = EFBMsg(self)
        txt = ("Friend request: {NickName}\n"
               "From: {Province}, {City}\n"
               "QQ: {QQNum}\n"
               "ID: {Alias}\n"
               "Signature: {Signature}\n"
               "Gender: {Sex}")
        tdict = msg['Text'].copy()
        tdict.update(msg['Text']['userInfo'])
        txt = txt.format(**tdict)
        mobj.text = txt
        mobj.type = MsgType.Command
        mobj.attributes = {
            "commands": [
                {
                    "name": "Send friend request",
                    "callable": "add_friend",
                    "args": [],
                    "kwargs": {
                        "userName": msg['Text']['userInfo']['UserName'],
                        "status": 3,
                        "ticket": msg['Ticket']
                    }
                }
            ]
        }
        return mobj

    def save_file(self, msg, msg_type):
        path = os.path.join("storage", self.channel_id)
        if not os.path.exists(path):
            os.makedirs(path)
        filename = "%s_%s_%s" % (msg_type, msg['NewMsgId'], int(time.time()))
        fullpath = os.path.join(path, filename)
        msg['Text'](fullpath)
        mime = magic.from_file(fullpath, mime=True)
        if isinstance(mime, bytes):
            mime = mime.decode()
        guess_ext = mimetypes.guess_extension(mime) or ".unknown"
        if guess_ext == ".unknown":
            self.logger.warning("File %s with mime %s has no matching extensions.", fullpath, mime)
        ext = ".jpeg" if mime == "image/jpeg" else guess_ext
        os.rename(fullpath, "%s%s" % (fullpath, ext))
        fullpath = "%s%s" % (fullpath, ext)
        self.logger.info("File saved from WeChat\nFull path: %s\nMIME: %s", fullpath, mime)
        return fullpath, mime

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
        UserName = self.get_UserName(msg.destination['uid'])
        if UserName is None or UserName is False:
            raise EFBChatNotFound
        r = None
        self.logger.info("Sending message to WeChat:\n"
                         "Target-------\n"
                         "uid: %s\n"
                         "UserName: %s\n"
                         "NickName: %s\n"
                         "Type: %s\n"
                         "Text: %s"
                         % (msg.destination['uid'], UserName, msg.destination['name'], msg.type, msg.text))
        if msg.type in [MsgType.Text, MsgType.Link]:
            if msg.target:
                if msg.target['type'] == TargetType.Member:
                    msg.text = "@%s\u2005 %s" % (msg.target['target'].member['alias'], msg.text)
                elif msg.target['type'] == TargetType.Message:
                    maxl = self._flag("max_quote_length", -1)
                    qt_txt = "%s" % msg.target['target'].text
                    if maxl > 0:
                        tgt_text = qt_txt[:maxl]
                        if len(qt_txt) >= maxl:
                            tgt_text += "…"
                        tgt_text = "「%s」" % tgt_text
                    elif maxl < 0:
                        tgt_text = "「%s」" % qt_txt
                    else:
                        tgt_text = ""
                    if UserName.startswith("@@"):
                        tgt_alias = "@%s\u2005 " % msg.target['target'].member['alias']
                    else:
                        tgt_alias = ""
                    msg.text = "%s%s\n\n%s" % (tgt_alias, tgt_text, msg.text)
            r = self._itchat_send_msg(msg.text, UserName)
        elif msg.type in [MsgType.Image, MsgType.Sticker]:
            self.logger.info("Image/Sticker %s, %s", msg.type, msg.path)
            if msg.mime in ["image/gif", "image/jpeg"]:
                try:
                    if os.path.getsize(msg.path) > 5 * 2 ** 20:
                        raise EFBMessageError("Image sent is too large. (IS01)")
                    self.logger.debug("Sending %s (image) to ItChat.", msg.path)
                    r = self._itchat_send_image(msg.path, UserName)
                    os.remove(msg.path)
                except FileNotFoundError:
                    pass
            else:  # Convert Image format
                img = Image.open(msg.path)
                try:
                    alpha = img.split()[3]
                    mask = Image.eval(alpha, lambda a: 255 if a <= 128 else 0)
                except IndexError:
                    mask = Image.eval(img.split()[0], lambda a: 0)
                img = img.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=255)
                img.paste(255, mask)
                img.save("%s.gif" % msg.path, transparency=255)
                msg.path = "%s.gif" % msg.path
                self.logger.info('Image converted to GIF: %s', msg.path)
                self.logger.debug("Sending %s (image) to ItChat.", msg.path)
                r = self._itchat_send_image(msg.path, UserName)
                os.remove(msg.path)
            if msg.text:
                self._itchat_send_msg(msg.text, UserName)
            self.logger.info('Image sent with result %s', r)
            if not msg.mime == "image/gif":
                try:
                    os.remove('.'.join(msg.path.split('.')[:-1]))
                except FileNotFoundError:
                    pass
        elif msg.type in (MsgType.File, MsgType.Audio):
            self.logger.info("Sending %s to WeChat\nFileName: %s\nPath: %s\nFilename: %s", msg.type, msg.text, msg.path,
                             msg.filename)
            r = self._itchat_send_file(msg.path, toUserName=UserName, filename=msg.filename)
            if msg.text:
                self._itchat_send_msg(msg.text, toUserName=UserName)
            os.remove(msg.path)
        elif msg.type == MsgType.Video:
            self.logger.info("Sending video to WeChat\nFileName: %s\nPath: %s", msg.text, msg.path)
            r = self._itchat_send_video(msg.path, UserName)
            if msg.text:
                self._itchat_send_msg(msg.text, UserName)
            os.remove(msg.path)
        else:
            raise EFBMessageTypeNotSupported()

        if isinstance(r, dict) and r.get('BaseResponse', dict()).get('Ret', -1) != 0:
            if r.get('BaseResponse', dict()).get('Ret', -1) == 1101:
                self.itchat.logout()
            raise EFBMessageError(str(r))
        else:
            msg.uid = r.get("MsgId", None)
            return msg

    # Extra functions

    @extra(name="Show chat list",
           desc="Get a list of chat from WeChat.\n"
                "Usage:\n    {function_name} [-r]\n"
                "    -r: Force refresh")
    def get_chat_list(self, param=""):
        refresh = False
        if param:
            if param == "-r":
                refresh = True
            else:
                return "Invalid command: %s." % param
        l = []
        for i in self.itchat.get_friends(refresh):
            l.append(i)
            l[-1]['Type'] = "User"

        for i in self.itchat.get_chatrooms(refresh):
            if not i['UserName'].startswith('@@'):
                continue
            l.append(i)
            l[-1]['Type'] = "Group"

        for i in self.itchat.get_mps(refresh):
            l.append(i)
            l[-1]['Type'] = "MP"

        msg = "List of chats:\n"
        for n, i in enumerate(l):
            alias = self._wechat_html_unescape(i.get('RemarkName', '') or i.get('DisplayName', ''))
            name = self._wechat_html_unescape(i.get('NickName', ''))
            x = "%s (%s)" % (alias, name) if alias else name
            msg += "\n%s: [%s] %s" % (n, x, i['Type'])

        return msg

    @extra(name="Set alias",
           desc="Set alias for a contact in WeChat. You may not set alias to a group or a MP contact.\n"
                "Usage:\n"
                "    {function_name} [-r] id [alias]\n"
                "    id: Chat ID (You may obtain it from \"Show chat list\" function.\n"
                "    alias: Alias to be set. Omit to remove.\n"
                "    -r: Force refresh")
    def set_alias(self, param=""):
        refresh = False
        if param:
            if param.startswith("-r "):
                refresh = True
                param = param[2:]
            param = param.split(maxsplit=1)
            if len(param) == 1:
                cid = param[0]
                alias = ""
            else:
                cid, alias = param
        else:
            return self.set_alias.desc

        if not cid.isdecimal():
            return "ID must be integer, \"%s\" given." % cid
        else:
            cid = int(cid)

        l = self.itchat.get_friends(refresh)

        if cid < 0:
            return "ID must between 0 and %s inclusive, %s given." % (len(l) - 1, cid)

        if cid >= len(l):
            return "You may not set alias to a group or a MP contact."

        self.itchat.set_alias(l[cid]['UserName'], alias)
        if alias:
            return "Chat \"%s\" is set with alias \"%s\"." % (l[cid]["NickName"], alias)
        else:
            return "Chat \"%s\" has removed its alias." % l[cid]["NickName"]

    @extra(name="\"Uin\" rate.",
           desc="For debug purpose only.\n"
                "Usage: {function_name}")
    def uin_rate(self, param=""):
        groups_uin = 0
        groups_all = 0
        members_uin = 0
        members_all = 0
        for i in self.itchat.get_chatrooms(True):
            groups_all += 1
            if i.get("Uin", None):
                groups_uin += 1
            if not i.get('MemberList', ''):
                i = self.itchat.update_chatroom(i.get('UserName', ''))
            for j in i['MemberList']:
                members_all += 1
                if j.get("Uin", None):
                    members_uin += 1

        users = self.itchat.get_friends(True) + self.itchat.get_mps(True)
        users_uin = len([i for i in users if i.get("Uin", None)])
        users_all = len(users) or 1
        groups_all = groups_all or 1
        members_all = members_all or 1

        return "`Uin` rate checkup.\n\n" \
               "Users + MP: %s/%s (%.2f%%)\n" \
               "Groups: %s/%s (%.2f%%)\n" \
               "Group Members: %s/%s (%.2f%%)" % \
               (users_uin, users_all, 100 * users_uin / users_all,
                groups_uin, groups_all, 100 * groups_uin / groups_all,
                members_uin, members_all, 100 * members_uin / members_all)

    @extra(name="Force log out",
           desc="Force log out WeChat session.\n"
                "Usage: {function_name}")
    def force_log_out(self, param=""):
        self.itchat.logout()
        return "Done."

    # Command functions

    def reauth(self, command=False):
        msg = "Starting authentication..."
        qr_reload = self._flag("qr_reload", "master_qr_code")
        if command and qr_reload == "console_qr_code":
            msg += "\nPlease visit your console or log for QR code and further instructions."

        def reauth_thread(self, qr_reload):
            qr_callback = getattr(self, qr_reload, self.master_qr_code)
            with self.mutex:
                self.itchat.auto_login(enableCmdQR=2,
                                       hotReload=True,
                                       statusStorageDir="storage/%s.pkl" % self.channel_id,
                                       exitCallback=self.exit_callback,
                                       qrCallback=qr_callback)
                self.done_reauth.set()

        threading.Thread(target=reauth_thread, args=(self, qr_reload)).start()
        return msg

    def add_friend(self, UserName=None, status=2, ticket="", UserInfo={}):
        if not UserName:
            return "Username is empty. (UE02)"
        try:
            self.itchat.add_friend(UserName, status, ticket, UserInfo)
            return "Success."
        except:
            return "Error occurred during the process. (AF01)"

    def get_chats(self, group=True, user=True):
        refresh = self._flag("refresh_friends", False)
        r = []
        if user:
            t = self.itchat.get_friends(refresh) + self.itchat.get_mps(refresh)
            t = [dict()] + t
            t[0]['NickName'] = "File Helper"
            t[0]['UserName'] = "filehelper"
            t[0]['RemarkName'] = ""
            t[0]['Uin'] = "filehelper"
            for i in t:
                if i['UserName'] == self.itchat.loginInfo['User']['UserName']:
                    continue
                r.append({
                    'channel_name': self.channel_name,
                    'channel_id': self.channel_id,
                    'name': self._wechat_html_unescape(i['NickName']),
                    'alias': self._wechat_html_unescape(i['RemarkName'] or i['NickName']),
                    'uid': self.get_uid(UserName=i['UserName'],
                                        NickName=self._wechat_html_unescape(i['NickName']),
                                        alias=self._wechat_html_unescape(i.get("RemarkName", None)),
                                        Uin=i.get("Uin", None)),
                    'type': MsgSource.User
                })
        if group:
            t = self.itchat.get_chatrooms(refresh)
            for i in t:
                if not i['UserName'].startswith('@@'):
                    continue
                r.append({
                    'channel_name': self.channel_name,
                    'channel_id': self.channel_id,
                    'name': self._wechat_html_unescape(i['NickName']),
                    'alias': self._wechat_html_unescape(i['RemarkName'] or i['NickName']),
                    'uid': self.get_uid(UserName=i['UserName'],
                                        NickName=self._wechat_html_unescape(i['NickName']),
                                        alias=self._wechat_html_unescape(i.get("RemarkName", None)),
                                        Uin=i.get("Uin", None)),
                    'type': MsgSource.Group
                })
        return r

    def get_itchat(self):
        return self.itchat

    def _flag(self, key, value):
        """
        Retrieve value for experimental flags.

        Args:
            key: Key of the flag.
            value: Default/fallback value.

        Returns:
            Value for the flag.
        """
        return getattr(config, self.channel_id, dict()).get('flags', dict()).get(key, value)

    @property
    def stop_polling(self):
        return self._stop_polling

    @stop_polling.setter
    def stop_polling(self, val):
        val = bool(val)
        if val and not self.itchat.alive:
            self.done_reauth.set()
        self._stop_polling = val

    def _itchat_send_msg(self, *args, **kwargs):
        try:
            return self.itchat.send_msg(*args, **kwargs)
        except Exception as e:
            raise EFBMessageError(repr(e))

    def _itchat_send_file(self, *args, **kwargs):
        def _itchat_send_fn(self, fileDir, toUserName=None, mediaId=None, filename=None):
            from itchat.returnvalues import ReturnValue
            from itchat import config
            import os, time, json
            if toUserName is None: toUserName = self.storageClass.userName
            if mediaId is None:
                r = self.upload_file(fileDir)
                if r:
                    mediaId = r['MediaId']
                else:
                    return r
            fn = filename or os.path.basename(fileDir)
            url = '%s/webwxsendappmsg?fun=async&f=json' % self.loginInfo['url']
            data = {
                'BaseRequest': self.loginInfo['BaseRequest'],
                'Msg': {
                    'Type': 6,
                    'Content': ("<appmsg appid='wxeb7ec651dd0aefa9' sdkver=''><title>%s</title>" % fn +
                                "<des></des><action></action><type>6</type><content></content><url></url><lowurl></lowurl>" +
                                "<appattach><totallen>%s</totallen><attachid>%s</attachid>" % (
                                    str(os.path.getsize(fileDir)), mediaId) +
                                "<fileext>%s</fileext></appattach><extinfo></extinfo></appmsg>" % fn[1].replace('.',
                                                                                                                '')),
                    'FromUserName': self.storageClass.userName,
                    'ToUserName': toUserName,
                    'LocalID': int(time.time() * 1e4),
                    'ClientMsgId': int(time.time() * 1e4), },
                'Scene': 0, }
            headers = {
                'User-Agent': config.USER_AGENT,
                'Content-Type': 'application/json;charset=UTF-8', }
            r = self.s.post(url, headers=headers,
                            data=json.dumps(data, ensure_ascii=False).encode('utf8'))
            return ReturnValue(rawResponse=r)

        try:
            _itchat_send_fn(self.itchat, *args, **kwargs)
        except Exception as e:
            raise EFBMessageError(repr(e))

    def _itchat_send_image(self, *args, **kwargs):
        try:
            return self.itchat.send_image(*args, **kwargs)
        except Exception as e:
            raise EFBMessageError(repr(e))

    def _itchat_send_video(self, *args, **kwargs):
        try:
            return self.itchat.send_video(*args, **kwargs)
        except Exception as e:
            raise EFBMessageError(repr(e))

    @staticmethod
    def _wechat_html_unescape(content):
        """
        Unescape a WeChat HTML string.

        Args:
            content (str): String to be formatted

        Returns:
            str: Unescaped string.
        """
        d = {"Content": content}
        itchat.utils.msg_formatter(d, "Content")
        return d['Content']