# encoding:utf-8
import json
import logging
import os
import urllib
import urllib2
import time
import pymongo
from db import database
from utils import Singleton
from BaseHandler import BaseHandler


class Message(object):
    """私信
        tpye:消息类型
        level:消息级别
        tpl_id:短消息模板id
        timeout:超时未读取发送短信通知
    """

    def __int__(self):
        self.timeout = 60 * 60 * 24

    @property
    def db(self):
        return database.database.getDB()

    def send(self, sender_id, sender_name, receiver_id, type, title, content):
        """
        发送私信
        type:消息类型
            1：投简历
            2：邀请面试
            3. 我有场地请联系我，邀请入孵
            4: 申请入孵
        """
        # id自增1,唯一id生成的方案 TODO
        last = self.db.message.find().sort("id", pymongo.DESCENDING).limit(1)
        if last.count() > 0:
            lastone = dict()
            for item in last:
                lastone = item
            message_id = int(lastone.get('id', 0)) + 1
        else:
            message_id = 1
        self.db.message.insert(
            {"id": message_id, "uid": sender_id, "sender_name": sender_name, "receiver_id": receiver_id, "type": type,
             "title": title, "content": content, "unread": 1, "time": time.strftime("%Y-%m-%d %H:%M:%S")})
        self.db.user.update({"uid": receiver_id}, {'$inc': {'unread': 1}})

        logging.info(("%s send message to %s,type is %d") % (sender_id, receiver_id, type))

    def read(self, user, id):
        """读取私信"""
        message = self.db.message.find_one({"uid": user['uid'], "id": id})
        message['unread'] = True
        self.db.message.update({"uid": user['uid']}, message)
        logging.info(("%u read message %d") % (user['name'], id))

    def remove(self, user, id):
        """删除私信"""
        message = self.db.message.find_one({"uid": user['uid'], "id": id})
        if message:
            message.remove()
            logging.warn(("message %d is be deleted,by user %s") % (id, user['name']))

    def timeout_unread(self):
        """消息超时未读"""
        pass
