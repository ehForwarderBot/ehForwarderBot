import os
import time
from . import config


class Storage:
    def __init__(self):
        self.userName = None
        self.nickName = None
        self.memberList = []
        self.chatroomList = []
        self.msgList = []
        self.groupDict = {}
        self.lastInputUserName = None

    def find_username(self, n):
        l = self.memberList + self.chatroomList
        for member in l:
            if member['NickName'] == n:
                return member['UserName']

    def find_nickname(self, u):
        l = self.memberList + self.chatroomList
        for member in l:
            if member['UserName'] == u:
                return member['NickName']

    def find_remarkname(self, u):
        l = self.memberList + self.chatroomList
        for member in l:
            if member['UserName'] == u:
                return member['RemarkName']
