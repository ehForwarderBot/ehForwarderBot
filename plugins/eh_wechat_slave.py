import io
import logging
import mimetypes
import os
import re
import time
import html
from binascii import crc32

import itchat
import magic
import xmltodict
from PIL import Image

import config
from channel import EFBChannel, EFBMsg, MsgType, MsgSource, TargetType, ChannelType
from channelExceptions import EFBMessageTypeNotSupported, EFBMessageError
from utils import extra


def incomeMsgMeta(func):
    def wcFunc(self, msg, isGroupChat=False):
        logger = logging.getLogger("plugins.%s.incomeMsgMeta" % self.channel_id)
        mobj = func(self, msg, isGroupChat)
        mobj.uid = msg.get("MsgId", time.time())
        me = msg['FromUserName'] == itchat.get_friends()[0]['UserName']
        logger.debug("me, %s", me)
        if me:
            msg['FromUserName'], msg['ToUserName'] = msg['ToUserName'], msg['FromUserName']
        FromUser = self.search_user(UserName=msg['FromUserName']) or \
                   [{"NickName": "Chat not found. (UE01)", "RemarkName": "Chat not found. (UE01)", "Uin": 0}]
        FromUser = FromUser[0]
        logger.debug("From user, %s", FromUser)
        if isGroupChat:
            logger.debug("groupchat")
            if me:
                msg['ActualUserName'] = msg['ToUserName']
                member = {"NickName": itchat.get_friends()[0]['NickName'], "DisplayName": "You", "Uin": itchat.get_friends()[0]['Uin']}
            else:
                logger.debug("search_user")
                member = self.search_user(UserName=msg['FromUserName'], ActualUserName=msg['ActualUserName'])[0]['MemberList'][0]
                logger.debug("search_user.done")
            mobj.source = MsgSource.Group
            logger.debug("Group. member: %s", member)
            mobj.origin = {
                'name': FromUser['NickName'],
                'alias': FromUser['RemarkName'] or FromUser['NickName'],
                'uid': self.get_uid(UserName=msg.get('FromUserName', None),
                                    NickName=html.unescape(FromUser.get('NickName', "s")),
                                    alias=html.unescape(FromUser.get('RemarkName', "s")),
                                    Uin=FromUser.get('Uin', None))
            }
            mobj.member = {
                'name': member['NickName'],
                'alias': member['DisplayName'],
                'uid': self.get_uid(UserName=msg.get('ActualUserName', None),
                                    NickName=html.unescape(member.get('NickName', "")),
                                    alias=html.unescape(member.get('DisplayName', "")),
                                    Uin=member.get('Uin', None))
            }
            logger.debug("origin: %s\nmember: %s\n", mobj.origin, mobj.member)
        else:
            if me:
                mobj.text = "You: " + mobj.text
            mobj.source = MsgSource.User
            mobj.origin = {
                'name': FromUser['NickName'],
                'alias': FromUser['RemarkName'] or FromUser['NickName'],
                'uid': self.get_uid(UserName=msg.get('FromUserName', None),
                                    NickName=html.unescape(FromUser.get('NickName', "")),
                                    alias=html.unescape(FromUser.get('RemarkName', "")),
                                    Uin=FromUser.get('Uin', None))
            }
        mobj.destination = {
            'name': itchat.get_friends()[0]['NickName'],
            'alias': itchat.get_friends()[0]['NickName'],
            'uid': self.get_uid(UserName=msg['ToUserName'])
        }
        logger.debug("dest: %s", mobj.destination)
        logger.info("WeChat incoming message:\nType: %s\nText: %s\nUserName: %s\nuid: %s\nname: %s" %
                    (mobj.type, msg['Text'], msg['FromUserName'], mobj.origin['uid'], mobj.origin['name']))
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
    supported_message_types = {MsgType.Text, MsgType.Sticker, MsgType.Image, MsgType.File, MsgType.Video, MsgType.Link}
    users = {}
    logger = logging.getLogger("plugins.%s.WeChatChannel" % channel_id)

    SYSTEM_USERNAMES = ["filehelper", "newsapp", "fmessage", "weibo", "qqmail", "fmessage", "tmessage", "qmessage",
                         "qqsync", "floatbottle", "lbsapp", "shakeapp", "medianote", "qqfriend", "readerapp",
                         "blogapp", "facebookapp", "masssendapp", "meishiapp", "feedsapp", "voip", "blogappweixin",
                         "weixin"]

    def __init__(self, queue):
        super().__init__(queue)
        itchat.auto_login(enableCmdQR=2,
                          hotReload=True,
                          statusStorageDir="storage/%s.pkl" % self.channel_id,
                          exitCallback=self.exit_callback,
                          qrCallback=self.console_qr_code)
        self.logger.info("EWS Inited!!!\n---")
        itchat.set_logging(showOnCmd=False)

    #
    # Utilities
    #

    def console_qr_code(self, uuid, status, qrcode):
        status = int(status)
        if status == 201:
            QR = 'Tap "Confirm" to continue.'
        elif status == 200:
            QR = "Successfully authorized."
        else:
            # 0: First QR code
            # 408: Updated QR code
            QR = "WeChat: Scan QR code with WeChat to continue. (%s, %s)\n" % (uuid, status)
            if status == 408:
                QR += "Previous code expired. Please scan the new one.\n"
            QR += "\n"
            time.sleep(0.5)
            img = Image.open(io.BytesIO(qrcode)).convert("1")
            img = img.resize((img.size[0] // 10, img.size[1] // 10))
            for i in range(img.size[0]):
                for j in range(img.size[1]):
                        if img.getpixel((i, j)) > 0:
                            QR += "\x1b[7m  \x1b[0m"
                        else:
                            QR += "\x1b[49m  \x1b[0m"
                QR += "\n"
            QR += "\nIf you cannot read the QR code above, " \
                  "Please generate a QR code with any tool with the following URL:\n" \
                  "https://login.weixin.qq.com/l/" + uuid

        self.logger.critical(QR)

    def exit_callback(self):
        msg = EFBMsg(self)
        msg.type = MsgType.Text
        msg.source = MsgSource.System
        msg.origin = {
            'name': 'WeChat System Message',
            'alias': 'WeChat System Message',
            'uid': -1
        }

        msg.text = "WeChat server logged out the user."

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
        if UserName in self.SYSTEM_USERNAMES:
            return UserName
        if not (UserName or NickName or alias or Uin):
            self.logger.error('No name provided.')
            return False
        fallback_order = self._flag("uid_order", ["NickName"])
        data = {"nickname": NickName, "alias": alias, "uin": Uin}
        if UserName and not (NickName or alias or Uin):
            r = self.search_user(UserName=UserName)
            if not r:
                self.logger.debug("get_uid, return False")
                return False
            data = {"nickname": r[0]['NickName'], "alias": r[0]["RemarkName"], "uin": r[0]["Uin"]}
        for i in fallback_order:
            if data[i.lower()]:
                return str(crc32(data[i.lower()].encode("utf-8")))
        return str(crc32(data[fallback_order[-1].lower()].encode("utf-8")))

    def get_UserName(self, uid, refresh=False):
        """
        Get WeChat `UserName` of a chat by UID.

        Args:
            uid (str): UID of the chat.
            refresh (bool): Refresh the chat list from WeChat, `False` by default.

        Returns:
            str|bool: `UserName` of the chosen chat. `False` if not found.
        """
        if uid in self.SYSTEM_USERNAMES:
            return uid
        r = self.search_user(uid=uid, refresh=refresh)
        if r:
            return r[0]['UserName']
        return False

    def search_user(self, UserName=None, uid=None, uin=None, name=None, ActualUserName=None, refresh=False):
        """
        Search for a WeChat "User" (a user, a group/chat room or an MPS account,
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
        fallback_order = self._flag("uid_order", ["NickName"])

        if all(i is None for i in [UserName, uid, uin, name]):
            raise ValueError("At least one of [UserName, uid, uin, name] should be provided.")

        if UserName in self.SYSTEM_USERNAMES or uin in self.SYSTEM_USERNAMES:
            sys_chat_id = UserName or uin
            return [{"UserName": sys_chat_id,
                     "NickName": "System (%s)" % sys_chat_id,
                     "RemarkName": "System (%s)" % sys_chat_id,
                     "Uin": sys_chat_id}]

        for i in itchat.get_friends(refresh) + itchat.get_mps(refresh):
            data = {"nickname": i.get('NickName', None),
                    "alias": i.get("RemarkName", None),
                    "uin": i.get("Uin", None)}
            for j in fallback_order:
                if str(crc32(data[j.lower()].encode("utf-8"))) == uid:
                    result.append(i.copy())
            if str(i.get('UserName', '')) == UserName or \
               str(i.get('AttrStatus', '')) == uid or \
               str(i.get('Uin', '')) == uin or \
               str(i.get('NickName', '')) == name or \
               str(i.get('DisplayName', '')) == name:
                result.append(i.copy())
        for i in itchat.get_chatrooms(refresh):
            if not i.get('MemberList', ''):
                i = itchat.update_chatroom(i.get('UserName', ''))
            data = {"nickname": i.get('NickName', None),
                    "alias": i.get("RemarkName", None),
                    "uin": i.get("Uin", None)}
            for j in fallback_order:
                if str(crc32(data[j.lower()].encode("utf-8"))) == uid:
                    result.append(i.copy())
            if str(i.get('Uin', '')) == uin or \
               str(i.get('NickName', '')) == name or \
               str(i.get('DisplayName', '')) == name or \
               str(i.get('UserName', '')) == UserName:
                result.append(i.copy())
                result[-1]['MemberList'] = []
                if ActualUserName:
                    for j in i['MemberList']:
                        data = {"nickname": j.get('NickName', None),
                                "alias": j.get("DisplayName", None),
                                "uin": j.get("Uin", None)}
                        for k in fallback_order:
                            if str(crc32(data[k.lower()].encode("utf-8"))) == uid:
                                result.append(k.copy())
                        if str(j['UserName']) == ActualUserName or \
                           str(j['AttrStatus']) == uid or \
                           str(j['NickName']) == name or \
                           str(j['DisplayName']) == name:
                            result[-1]['MemberList'].append(j)
        if not result and not refresh:
            return self.search_user(UserName, uid, uin, name, ActualUserName, refresh=True)
        return result

    def poll(self):
        self.usersdata = itchat.get_friends(True) + itchat.get_chatrooms()

        @itchat.msg_register(['Text'], isFriendChat=True, isMpChat=True)
        def wcText(msg):
            self.textMsg(msg)

        @itchat.msg_register(['Text'], isGroupChat=True)
        def wcTextGroup(msg):
            self.logger.info("text Msg from group %s", msg['Text'])
            self.textMsg(msg, True)

        @itchat.msg_register(['Sharing'], isFriendChat=True, isMpChat=True)
        def wcLink(msg):
            self.linkMsg(msg)

        @itchat.msg_register(['Sharing'], isGroupChat=True)
        def wcLinkGroup(msg):
            self.linkMsg(msg, True)

        @itchat.msg_register(['Picture'], isFriendChat=True, isMpChat=True)
        def wcPicture(msg):
            self.pictureMsg(msg)

        @itchat.msg_register(['Picture'], isGroupChat=True)
        def wcPictureGroup(msg):
            self.pictureMsg(msg, True)

        @itchat.msg_register(['Attachment'], isFriendChat=True, isMpChat=True)
        def wcFile(msg):
            self.fileMsg(msg)

        @itchat.msg_register(['Attachment'], isGroupChat=True)
        def wcFileGroup(msg):
            self.fileMsg(msg, True)

        @itchat.msg_register(['Recording'], isFriendChat=True, isMpChat=True)
        def wcRecording(msg):
            self.voiceMsg(msg)

        @itchat.msg_register(['Recording'], isGroupChat=True)
        def wcRecordingGroup(msg):
            self.voiceMsg(msg, True)

        @itchat.msg_register(['Map'], isFriendChat=True, isMpChat=True)
        def wcLocation(msg):
            self.locationMsg(msg)

        @itchat.msg_register(['Map'], isGroupChat=True)
        def wcLocationGroup(msg):
            self.locationMsg(msg, True)

        @itchat.msg_register(['Video'], isFriendChat=True, isMpChat=True)
        def wcVideo(msg):
            self.videoMsg(msg)

        @itchat.msg_register(['Video'], isGroupChat=True)
        def wcVideoGroup(msg):
            self.videoMsg(msg, True)

        @itchat.msg_register(['Card'], isFriendChat=True, isMpChat=True)
        def wcCard(msg):
            self.cardMsg(msg)

        @itchat.msg_register(['Card'], isGroupChat=True)
        def wcCardGroup(msg):
            self.cardMsg(msg, True)

        @itchat.msg_register(['Friends'], isFriendChat=True, isMpChat=True)
        def wcFriends(msg):
            self.friendMsg(msg)

        @itchat.msg_register(['Friends'], isGroupChat=True)
        def wcFriendsGroup(msg):
            self.friendMsg(msg, True)

        @itchat.msg_register(['Useless', 'Note'], isFriendChat=True, isMpChat=True)
        def wcSystem(msg):
            self.systemMsg(msg)

        @itchat.msg_register(['Useless', 'Note'], isGroupChat=True)
        def wcSystemGroup(msg):
            self.systemMsg(msg, True)

        @itchat.msg_register(["System"])
        def wcSysLog(msg):
            self.logger.debug("WeChat \"System\" message:\n%s", repr(msg))

        itchat.run()
        # while True:
        #     if not itchat.client().status:
        #         msg = EFBMsg(self)
        #         msg.type = MsgType.Text
        #         msg.source = MsgType.System
        #         msg.origin = {
        #             "name": "EFB System",
        #             "alias": "EFB System",
        #             "uid": None
        #         }
        #         mobj.destination = {
        #             'name': itchat.client().storageClass.nickName,
        #             'alias': itchat.client().storageClass.nickName,
        #             'uid': self.get_uid(NickName=itchat.client().storageClass.userName)
        #         }
        #         msg.text = "Logged out unexpectedly."

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
    def systemMsg(self, msg, isGroupChat=False):
        mobj = EFBMsg(self)
        mobj.text = "System message: %s" % msg['Text']
        mobj.type = MsgType.Text
        return mobj

    @incomeMsgMeta
    def locationMsg(self, msg, isGroupChat):
        mobj = EFBMsg(self)
        mobj.text = msg['Content'].split('\n')[0][:-1]
        loc = re.search("=-?([0-9.]+),-?([0-9.]+)", msg['Url']).groups()
        mobj.attributes = {"longitude": float(loc[1]), "latitude": float(loc[0])}
        mobj.type = MsgType.Location
        return mobj

    @incomeMsgMeta
    def linkMsg(self, msg, isGroupChat=False):
        self.logger.info("---\nNew Link msg, %s", msg)
        # initiate object
        mobj = EFBMsg(self)
        # parse XML
        itchat.utils.emoji_formatter(msg, 'Content')
        xmldata = msg['Content']
        data = xmltodict.parse(xmldata)
        # set attributes
        mobj.attributes = {
            "title": data['msg']['appmsg']['title'],
            "description": data['msg']['appmsg']['des'],
            "image": data['msg']['appmsg']['thumburl'],
            "url": data['msg']['appmsg']['url']
        }
        # format text
        mobj.text = ""
        if self._flag("extra_links_on_message", False):
            extra_link = data.get('msg', {}).get('appmsg', {}).get('mmreader', {}).get('category', {}).get('item', [])
            if type(extra_link) is list and len(extra_link):
                for i in extra_link:
                    mobj.text += "🔗 %s\n%s\n%s\n🖼 %s\n\n" % (i['title'], i['digest'], i['url'], i['cover'])
        mobj.type = MsgType.Link
        return mobj

    @incomeMsgMeta
    def pictureMsg(self, msg, isGroupChat=False):
        mobj = EFBMsg(self)
        mobj.type = MsgType.Image if msg['MsgType'] == 3 else MsgType.Sticker
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

    @incomeMsgMeta
    def cardMsg(self, msg, isGroupChat=False):
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

    @incomeMsgMeta
    def friendMsg(self, msg, isGroupChat=False):
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
        if type(mime) is bytes:
            mime = mime.decode()
        ext = "jpg" if mime == "image/jpeg" else mimetypes.guess_extension(mime)
        os.rename(fullpath, "%s.%s" % (fullpath, ext))
        fullpath = "%s.%s" % (fullpath, ext)
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
                    msg.text = "@%s\u2005 「%s」\n\n%s" % (msg.target['target'].member['alias'], msg.target['target'].text, msg.text)
            r = itchat.send(msg.text, UserName)
        elif msg.type in [MsgType.Image, MsgType.Sticker]:
            self.logger.info("Image/Sticker %s", msg.type)
            if msg.mime in ["image/gif", "image/jpeg"]:
                r = itchat.send_image(msg.path, UserName)
                os.remove(msg.path)
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
                self.logger.info('Sending Image...')
                r = itchat.send_image(msg.path, UserName)
                if msg.text:
                    itchat.send_msg(msg.text, UserName)
                os.remove(msg.path)
            self.logger.info('Image sent with result %s', r)
            if not msg.mime == "image/gif":
                try:
                    os.remove('.'.join(msg.path.split('.')[:-1]))
                except FileNotFoundError:
                    pass
        elif msg.type in [MsgType.File, MsgType.Video]:
            self.logger.info("Sending file to WeChat\nFileName: %s\nPath: %s", msg.text, msg.path)
            r = itchat.send_file(msg.path, UserName)
            if msg.text:
                itchat.send_msg(msg.text, UserName)
            os.remove(msg.path)
        else:
            raise EFBMessageTypeNotSupported()

        if r.get('BaseResponse', []).get('Ret', -1) != 0:
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
        for i in itchat.get_friends(refresh)[1:]:
            l.append(i)
            l[-1]['Type'] = "User"

        for i in itchat.get_chatrooms(refresh):
            l.append(i)
            l[-1]['Type'] = "Group"

        for i in itchat.get_mps(refresh):
            l.append(i)
            l[-1]['Type'] = "MPS"

        msg = "List of chats:\n"
        for n, i in enumerate(l):
            alias = i.get('RemarkName', '') or i.get('DisplayName', '')
            name = i.get('NickName', '')
            x = "%s (%s)" % (alias, name) if alias else name
            msg += "\n%s: [%s] %s" % (n, x, i['Type'])

        return msg

    @extra(name="Set alias",
           desc="Set alias for a contact in WeChat. You may not set alias to a group or a MPS contact.\n"
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

        l = itchat.get_friends(refresh)[1:]

        if cid < 0:
            return "ID must between 0 and %s inclusive, %s given." % (len(l) - 1, cid)

        if cid >= len(l):
            return "You may not set alias to a group or a MPS contact."

        itchat.set_alias(l[cid]['UserName'], alias)
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
        for i in itchat.get_chatrooms(True):
            groups_all += 1
            if i.get("Uin", None):
                groups_uin += 1
            if not i.get('MemberList', ''):
                i = itchat.update_chatroom(i.get('UserName', ''))
            for j in i['MemberList']:
                members_all += 1
                if j.get("Uin", None):
                    members_uin += 1

        users = itchat.get_friends(True) + itchat.get_mps(True)
        users_uin = len([i for i in users if i.get("Uin", None)])
        users_all = len(users)

        return "`Uin` rate checkup.\n\n" \
               "Users + MPS: %s/%s (%.2f%%)\n" \
               "Groups: %s/%s (%.2f%%)\n" \
               "Group Members: %s/%s (%.2f%%)" % \
               (users_uin, users_all, 100 * users_uin / users_all,
                groups_uin, groups_all, 100 * groups_uin / groups_all,
                members_uin, members_all, 100 * members_uin / members_all)

    # Command functions

    def add_friend(self, UserName=None, status=2, ticket="", UserInfo={}):
        if not UserName:
            return "Username is empty. (UE02)"
        try:
            itchat.add_friend(UserName, status, ticket, UserInfo)
            return "Success."
        except:
            return "Error occurred during the process. (AF01)"

    def get_chats(self, group=True, user=True):
        refresh = self._flag("refresh_friends", False)
        r = []
        if user:
            t = itchat.get_friends(refresh) + itchat.get_mps(refresh)
            t[0]['NickName'] = "File Helper"
            t[0]['UserName'] = "filehelper"
            t[0]['RemarkName'] = ""
            t[0]['Uin'] = "filehelper"
            for i in t:
                r.append({
                    'channel_name': self.channel_name,
                    'channel_id': self.channel_id,
                    'name': i['NickName'],
                    'alias': i['RemarkName'] or i['NickName'],
                    'uid': self.get_uid(UserName=i['UserName'], NickName=i['NickName'], alias=i.get("RemarkName", None), Uin=i.get("Uin", None)),
                    'type': MsgSource.User
                })
        if group:
            t = itchat.get_chatrooms(refresh)
            for i in t:
                r.append({
                    'channel_name': self.channel_name,
                    'channel_id': self.channel_id,
                    'name': i['NickName'],
                    'alias': i['RemarkName'] or i['NickName'] or None,
                    'uid': self.get_uid(NickName=i['NickName'], alias=i.get("RemarkName", None), Uin=i.get("Uin", None)),
                    'type': MsgSource.Group
                })
        return r

    def get_itchat(self):
        return itchat

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