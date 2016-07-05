# -*- coding: utf-8 -*-
from __future__ import division
import random
import tornado.web
from db import database
from db.redis_connection import _connect_redis


class LoginStateModule(tornado.web.UIModule):
    def render(self):
        return self.render_string("login-state.html", myuser="")


class HeaderModule(tornado.web.UIModule):
    def render(self, tab, myuser):
        return self.render_string("header.html", current_tab=tab, myuser=myuser)


class RandomStrModule(tornado.web.UIModule):
    def render(self):
        return random.randrange(1000, 5000)

class GetUserNameById(tornado.web.UIModule):
    def render(self, uid):
        user = database.database.getDB().user.find_one({"uid": uid})

        if user:
            return user['name']
        else:
            return ""


class NoticeModule(tornado.web.UIModule):
    def render(self, notice):
        return self.render_string("module/notice.html", n=notice)


class MessageModule(tornado.web.UIModule):
    def render(self, message):
        db = database.database.getDB()

        def user_info(uid):
            return db.user.find_one({"uid": uid}, {"pwd": 0})

        return self.render_string("module/message.html", m=message, user_info=user_info)


class Unread(tornado.web.UIModule):
    def render(self, user):
        db = database.database.getDB()
        if user == None:
            return ""
        return db.notice.find({"uid": user['uid'], "unread": 1}).count() + db.message.find(
            {"receiver_id": user['uid'], "unread": 1}).count()




class Percent(tornado.web.UIModule):
    """计算百分比"""

    def render(self, a, b):
        return int(a) / int(b) * 100


class Add(tornado.web.UIModule):
    def render(self, a, b):
        return int(a) + int(b)


class Multi(tornado.web.UIModule):
    """乘法"""

    def render(self, a, b):
        return int(a) * int(b)


