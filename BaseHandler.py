# encoding:utf-8
import functools
import os
import time
from urllib import urlencode
import urlparse
import logging
import pymongo

import tornado.web
from tornado.web import HTTPError
# from raven.contrib.tornado import SentryMixin
from db import database
from utils.session import *


class BaseHandler(tornado.web.RequestHandler):
    def __init__(self, *argc, **argkw):
        super(BaseHandler, self).__init__(*argc, **argkw)
        self.session = Session(self.application.session_manager, self)

    def get_current_user(self):
        return self.session.get("uid")

    @property
    def get_session(self):
        return self.session

    def auth(self):
        if not self.session:
            self.redirect('/login')

    @property
    def db(self):
        return database.database.getDB()

    def update_object_id(self, object_id, table, info):
        if object_id:
            object = self.db[table].find_one({"id": int(object_id)})
            if object['uid'] != self.user['uid']:
                raise HTTPError(403)
            info['id'] = int(object_id)
            # self.db[table].update({"id": int(object_id)}, info)
        else:
            last = self.db[table].find().sort("id", pymongo.DESCENDING).limit(1)
            if last.count() > 0:
                lastone = dict()
                for item in last:
                    lastone = item
                info['id'] = int(lastone['id']) + 1
            else:
                info['id'] = 1
        return info

    @property
    def logging(self):
        logging.basicConfig(level=logging.WARN,
                            format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S',
                            filename=os.path.join(os.path.dirname(__file__), "log") + "web.log",
                            filemode='w')
        return logging

    def handle_log(self, msg):
        msg['time'] = time.strftime("%Y-%m-%d %H:%M:%S")
        msg['time_stamp'] = time.time()
        self.db.user_handle.insert(msg)
        return True

    @property
    def user(self):
        if self.session.get("uid"):
            name = self.session.get("uid")
            # return self.session['data']
            if self.session.get("uid") == 'admin':
                return self.db.user.find_one({"username": self.session.get("uid")})
            return self.db.user.find_one({"$or": [{'username': name}, {"uid": name}, {'phone': name}]})
        else:
            return None

    @property
    def unread_notice(self):
        if self.user:
            notices = self.db.notice.find({"uid": self.user['uid'], "unread": 1})
            return notices.count()
        else:
            return 0

    def begin_session(self, name, password):
        # name为手机号
        self.logging.info(('start login', name, password))
        if not self.application.auth.log_in(name, password):
            print "login failed"
            return False
        self.logging.info(('login checked', name, password))
        now = time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time()))
        self.db.user.update({'username': name}, {'$set': {'lasttime': now, 'status': 'online'}})
        # user = self.db.user.find_one({'uid': username}, {'pwd': 0, '_id': 0})
        # user = self.db.user.find_one({'uid': name}, {'pwd': 0, '_id': 0})
        user = self.db.user.find_one({'phone': name}, {'pwd': 0, '_id': 0})
        data = user
        self.logging.info(('login', data))

        # id = self.application.sessions.new_session(data).hex
        # self.session = self.application.sessions.get_session(id)
        # self.set_cookie('id', id, httponly=True)

        self.session['data'] = user
        self.session["uid"] = name
        self.session.save()
        return True

    def begin_admin_session(self, username, password):
        self.logging.info(('start login', username, password))
        if not self.application.auth.admin_log_in(username, password):
            print "login failed"
            return False
        self.logging.info(('login checked', username, password))
        now = time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time()))
        self.db.user.update({'username': username}, {'$set': {'lasttime': now, 'status': 'online'}})
        # user = self.db.user.find_one({'uid': username}, {'pwd': 0, '_id': 0})
        user = self.db.user.find_one({'username': username}, {'pwd': 0, '_id': 0})
        data = user
        self.logging.info(('login', data))

        # id = self.application.sessions.new_session(data).hex
        # self.session = self.application.sessions.get_session(id)
        # self.set_cookie('id', id, httponly=True)

        self.session['data'] = user
        self.session["uid"] = username
        self.session.save()
        return True

    def setMenuID(self, mid):
        recode = self.session

    def end_session(self):
        id = self.get_cookie('id')
        self.application.sessions.clear_session(id)
        if self.session is not None:
            if self.session.get("uid"):
                # username = self.session['data']['uid']
                username = self.session.get("uid")
                # self.db.user.update({'uid': username}, {'$set': {'status': 'offline'}})
                self.application.auth.log_out(username)
        self.session['uid'] = None
        # self.clear_cookie('id')
        self.session.save()

    def write_error(self, status_code, **kwargs):
        if status_code == 404:
            print "404"
            self.render('404.html')
        elif status_code == 403:
            self.render('403.html')
        elif status_code == 500:
            self.render('500.html')
        else:
            self.write('error:' + str(status_code))

    @classmethod
    def authenticated(self, method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            if not self.user:
                url = self.get_login_url()
                self.redirect(url)
                return
            if not self.session.get('uid'):
                if self.request.method in ("GET", "HEAD"):
                    url = self.get_login_url()
                    if "?" not in url:
                        if urlparse.urlsplit(url).scheme:
                            # if login url is absolute, make next absolute too
                            next_url = self.request.full_url()
                        else:
                            next_url = self.request.uri
                        url += "?" + urlencode(dict(next=next_url))
                    self.redirect(url)
                    return
                    # 不抛异常
                    # raise HTTPError(403)
            # current_hour = int(time.strftime('%H', time.localtime(time.time())))
            # current_minute = int(time.strftime('%M', time.localtime(time.time())))
            # if current_hour >= 12 and current_hour <= 13:
            #
            #     self.render("pause.html")
            #     return
            return method(self, *args, **kwargs)

        return wrapper

    @classmethod
    def check_safe_pwd(self, method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            # print self.session.get('safe_pwd', '') == self.user.get("safe_pwd")
            if not self.user:
                self.redirect("/login")
                return
            cookie_safe_pwd = self.get_secure_cookie("safe_pwd")
            if not cookie_safe_pwd or cookie_safe_pwd != self.user.get("safe_pwd"):
                url = '/account/safe_pwd_check' + "?" + urlencode(dict(next=self.request.uri))
                self.redirect(url)
                return
            return method(self, *args, **kwargs)

        return wrapper

    @classmethod
    def check_info(self, method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            wechat = self.user.get("wechat", "")
            alipay = self.user.get("alipay", "")
            bankname = self.user.get("bank", {}).get("name")  # 银行卡类型
            BankCard = self.user.get("bank", {}).get("card")  # 银行卡卡号
            BankUserName = self.user.get("bank", {}).get("user_name")  # 银行卡用户名
            BankAddress = self.user.get("bank", {}).get("address")  # 银行卡地址
            # if "" in [wechat, alipay]:
            #     self.render("ok.html", url="/account/info_setting", tip="请填写微信号")
            if None in [BankCard, bankname, BankUserName, BankAddress]:
                self.render("ok.html", url="/account/info_setting", tip="请完善银行卡信息")

            return method(self, *args, **kwargs)

        return wrapper

    @classmethod
    def is_check(self, method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            if not self.user:
                url = self.get_login_url()
                if urlparse.urlsplit(url).scheme:
                    # if login url is absolute, make next absolute too
                    next_url = self.request.full_url()
                else:
                    next_url = self.request.uri
                url += "?" + urlencode(dict(next=next_url))
            if not self.user.get("is_active"):
                self.render("redirect_index.html", url=url, tip="玩家请于上家联系激活 激活成功后才可进行操作")

            return method(self, *args, **kwargs)

        return wrapper

    @classmethod
    def is_active(self, method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):

            if not self.user.get("is_active"):
                self.render("ok.html", url="/user/home", tip="玩家请于上家联系激活 激活成功后才可进行操作")

            return method(self, *args, **kwargs)

        return wrapper

    @classmethod
    def check_pwd_protect(self, method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            if not self.user:
                url = self.get_login_url()
                return self.redirect(url)
            if None in [self.user.get("question"), self.user.get('answer')]:
                self.render("ok.html", url="/account/pwd_protect", tip="请先设置密保信息")

            return method(self, *args, **kwargs)

        return wrapper

    @classmethod
    def duration_rest(self, method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            if not self.user:
                url = self.get_login_url()
                return self.redirect(url)
            current_hour = int(time.strftime('%H', time.localtime(time.time())))
            current_minute = int(time.strftime('%M', time.localtime(time.time())))
            if current_hour >= 0 and current_hour <= 1:
                self.render("rest.html")
                return
            return method(self, *args, **kwargs)

        return wrapper

    @classmethod
    def matching(self, method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            if not self.user:
                url = self.get_login_url()
                return self.redirect(url)
            current_hour = int(time.strftime('%H', time.localtime(time.time())))
            current_minute = int(time.strftime('%M', time.localtime(time.time())))
            if current_hour >= 12 and current_hour <= 13:
                self.render("matching.html")
                return
            return method(self, *args, **kwargs)

        return wrapper

    def get_admin_login_url(self):

        self.require_setting("admin_login_url", "@admin_authed")
        return self.application.settings["admin_login_url"]

    @classmethod
    def admin_authed(self, method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            if not self.session:
                if self.request.method in ("GET", "HEAD"):
                    url = self.get_admin_login_url()
                    if "?" not in url:
                        if urlparse.urlsplit(url).scheme:
                            # if login url is absolute, make next absolute too
                            next_url = self.request.full_url()
                        else:
                            next_url = self.request.uri
                        url += "?" + urlencode(dict(next=next_url))
                    self.redirect(url)
                    return
                raise HTTPError(403)
            else:
                if self.session['data'].get("role", "") != "superadmin":
                    # raise HTTPError(403)
                    # self.redirect('/admin/login')
                    return
            return method(self, *args, **kwargs)

        return wrapper
