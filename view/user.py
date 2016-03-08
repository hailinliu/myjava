# -*- coding: utf-8 -*-
from __future__ import division
import json
import logging
import os
import random
import time
import uuid
from bson import DBRef, ObjectId
import datetime
from passlib.handlers.pbkdf2 import pbkdf2_sha512
from datetime import date
import pymongo
from tornado.web import HTTPError

from BaseHandler import BaseHandler
from utils import send_short_msg, random_code
from utils.Message import Message
from utils.mail import MailHandler
from utils.uploadsets import process_question
from utils.wrapper import fn_timer
import string


# 注册验证码
class RegisterSendCode(BaseHandler):
    """发送注册验证码"""

    def get(self):
        mobile_number = self.get_argument("mobile_number")
        msg_code = random.randint(100000, 999999)
        self.set_cookie('msg_code', str(msg_code))
        print self.get_cookie('msg_code')

        last_request_time = datetime.datetime.now() - datetime.timedelta(minutes=1)
        # 查找一分钟内的register 验证码请求记录
        record = self.db.request_record.find_one(
            {"type": "register", "ip": self.request.remote_ip, "time": {"$gte": last_request_time}})
        permit = False if record else True
        if permit:
            tpl_value = "#code#=%s" % (str(msg_code))
            print tpl_value
            send_short_msg('908659', tpl_value, mobile_number)
            # 写入请求记录表
            self.db.request_record.insert(
                {"time": datetime.datetime.now(), "type": "register", "ip": self.request.remote_ip})
            self.write(json.dumps({"msg": 'ok', "error": ''}))
        else:
            self.write(json.dumps({"msg": '请勿频繁请求', "error": 'error'}))


class ResetPwdHandler(BaseHandler):
    """修改密码"""

    def get(self):
        pass

    @BaseHandler.authenticated
    def post(self):
        opwd = self.get_argument('opwd', None)
        npwd = self.get_argument('npwd', None)
        if "" in [opwd, npwd]:
            self.write(json.dumps({"status": "error", "msg": u"密码不能为空"}))

        # 旧密码验证
        if not self.application.auth.log_in(self.user['name'], opwd):
            self.write(json.dumps({"status": "error", "msg": u"密码不正确"}))

        # 新密码写入
        if not self.application.auth.changepwd(self.user['uid'], npwd):
            self.write(json.dumps({"status": "ok", "msg": u"error"}))
        else:
            self.write(json.dumps({"status": "ok", "msg": u"密码已修改"}))


class ForgetPwdHandler(BaseHandler):
    """忘记密码"""

    def get(self):
        pass

    @BaseHandler.authenticated
    def post(self):
        pass


class UserHomeHandler(BaseHandler):
    """会员中心"""

    @BaseHandler.authenticated
    def get(self):
        self.render("user/home.html", myuser=self.user, account_tab=1)


class MyFarm(BaseHandler):
    """我的农场"""

    @BaseHandler.authenticated
    def get(self):
        self.render("farm/mynongchang.html", myuser=self.user, account_tab=2)


def this_year():
    return date.today().year


class MyLoginInfoHandler(BaseHandler):
    """我的登录信息"""

    @BaseHandler.authenticated
    def get(self):
        page_arg = self.get_argument("page", 1)
        current_page = int(page_arg)
        next_page = current_page + 1
        counts = self.db.logininfo.find({"uid": self.user['uid']}).count()
        per = 10
        pages = int(round(counts / per))
        if current_page % 5 != 0:
            start_index = int((current_page / 5)) * 5 + 1
        else:
            start_index = int((current_page / 5) - 1) * 5 + 1
        logininfos = self.db.logininfo.find({"uid": self.user['uid']}). \
            skip(per * current_page).sort("_id", pymongo.DESCENDING).limit(10)
        self.render("user/user-logininfo.html", myuser=self.user, logininfos=logininfos, current_page=current_page,
                    start_index=start_index, next_page=next_page, page_count=pages, account_tab=9)


class SafeSettingHandler(BaseHandler):
    """安全设置"""

    @BaseHandler.authenticated
    def get(self):
        myuser = self.db.user.find_one({"uid": self.user['uid']})
        LPhone = str(myuser['phone'])[0:3]
        Rphone = str(myuser['phone'])[-3:]
        phone = LPhone + "*****" + Rphone
        Lemail = str(myuser['email'])[0:3]
        Remail = str(myuser['email'])[-4:]
        email = Lemail + "****@**" + Remail
        type = self.get_argument("type", None)
        id_verify = self.db.id_verify.find_one({"uid": self.user["uid"]})
        if not id_verify:
            id_verify = {}
        # print phone
        # print email
        self.render("user/user-safe-setting.html", myuser=self.user, id_verify=id_verify, type=type, account_tab=9,
                    phone=phone, email=email)

    def post(self):

        type = self.get_argument("type", "")
        if type == "login_pwd":
            opwd = self.get_argument('opwd', None)
            npwd = self.get_argument('npwd', None)
            npwd2 = self.get_argument('npwd2', None)
            if "" in [opwd, npwd, npwd2]:
                print "pwd is null"
                return self.write(json.dumps({"status": "error", "msg": u"密码不能为空"}))
            if npwd != npwd2:
                print "npwd is difference"
                return self.write(json.dumps({"static": "error", "msg": u"新密码不一致，请重新输入"}))
            else:
                # 旧密码验证
                if not self.application.auth.log_in(self.user['name'], opwd):
                    self.write(json.dumps({"status": "error", "msg": u"密码不正确"}))
                # 新密码写入
                if not self.application.auth.changepwd(self.user['uid'], npwd):
                    print "login_pwd updated"
                    self.write(json.dumps({"status": "error", "msg": u"error"}))
                else:
                    self.write(json.dumps({"status": "ok", "msg": u"密码已修改"}))

        elif type == "phone":
            # print "phone"
            old_phone = self.get_argument('old_phone', None)
            new_phone = self.get_argument('new_phone', None)
            phone_code = self.get_argument('phone_code', None)
            user = self.db.user.find_one({"uid": self.user['uid']})

            # print old_phone, new_phone, phone_code
            # 旧手机号码验证
            if old_phone != user['phone']:
                return self.write(json.dumps({"status": "error", "msg": u"原手机号码不正确"}))
            if old_phone == new_phone:
                return self.write(json.dumps({"status": "error", "msg": u"新号码和旧号码不能一致"}))
            if phone_code != self.get_cookie('msg_code'):
                return self.write(json.dumps({"msg": u'手机验证码输入错误', "error": 'error'}))
            # 新手机号写入
            else:
                if not self.application.auth.changephone(self.user['uid'], new_phone):
                    print "login_phone updated"
                    return self.write(json.dumps({"msg": u"修改手机号失败", "error": 'error'}))
                else:
                    return self.write(json.dumps({"status": "ok", "msg": u"修改手机号码成功"}))

        elif type == "email":
            # print "email"
            old_email = self.get_argument('old_email', None)
            new_email = self.get_argument('new_email', None)
            email_code = self.get_argument('email_code', None)
            user = self.db.user.find_one({"uid": self.user['uid']})
            # 旧邮箱验证
            if old_email != user['email']:
                return self.write(json.dumps({"status": "error", "msg": u"原邮箱帐号不正确"}))
            if old_email == new_email:
                return self.write(json.dumps({"status": "error", "msg": u"新邮箱和旧邮箱不能一致"}))

            if email_code != self.get_cookie('email_code'):
                return self.write(json.dumps({"msg": u'邮箱验证码输入错误', "error": 'error'}))
            # 新邮箱号写入
            else:
                if not self.application.auth.changeemail(self.user['uid'], new_email):
                    print "user_email updated"
                    return self.write(json.dumps({"msg": u"修改邮箱失败", "error": 'error'}))
                else:
                    self.db.user.update({"uid": self.user['uid']}, {"$set": {"email_check": 1}})
                    return self.write(json.dumps({"status": "ok", "msg": u"修改邮箱成功"}))

        elif type == "pay_pwd":
            print "pay_pwd"
            old_pay_pwd = self.get_argument('old_pay_pwd', "")
            new_pay_pwd = self.get_argument('new_pay_pwd', "")
            pwd_code = self.get_argument('paypwd_code', "")
            cookiecode = self.get_secure_cookie('verify_code')
            print pwd_code
            print cookiecode
            if "" in [old_pay_pwd, new_pay_pwd]:
                print "pay_pwd is null"
                return self.write(json.dumps({"status": "error", "msg": u"支付密码不能为空"}))
            if pwd_code != cookiecode:
                print "pwd_code != cookiecode"
                return self.write(json.dumps({"status": "error", "msg": u"验证码错误"}))
            else:
                user = self.db.user.find_one({"uid": self.user['uid']})
                login_pwd = user.get("pwd")

                if not user.get("pay_pwd", None):
                    rs = pbkdf2_sha512.verify(old_pay_pwd, login_pwd)
                    print "pay_pwd", user.get("pay_pwd")
                else:
                    rs = pbkdf2_sha512.verify(old_pay_pwd, user.get("pay_pwd"))
                    print rs
                if rs:
                    if self.application.auth.changepaypwd(self.user['uid'], new_pay_pwd):
                        user = self.db.user.find_one({"uid": self.user['uid']})
                        print user.get("pay_pwd")
                        return self.write(json.dumps({"status": "ok", "msg": u"支付密码更新成功"}))
                else:
                    return self.write(json.dumps({"status": "error", "msg": u"原支付密码不正确"}))
        else:
            self.write(json.dumps({"status": "error", "msg": u"参数错误"}))


class MessageCenter(BaseHandler):
    """消息中心"""

    @BaseHandler.authenticated
    def get(self):

        page_arg = self.get_argument("page", 1)
        type = self.get_argument("type", "notice")
        current_page = int(page_arg)
        next_page = current_page + 1
        notice_counts = self.db.notice.find({"uid": self.user['uid']}).count()
        messages_count = self.db.message.find({"uid": self.user['uid']}).count()
        per = 5
        notice_counts = int(round(notice_counts / per))
        if notice_counts == 0:
            notice_counts = 1
        messages_counts = int(round(messages_count / per))
        if messages_count == 0:
            messages_counts = 1
        if current_page % per != 0:
            start_index = int((current_page / per)) * per + 1
        else:
            start_index = int((current_page / per) - 1) * per + 1

        unread_notices = self.db.notice.find({"uid": self.user['uid'], "unread": 1})
        unread_messages = self.db.message.find({"receiver_id": self.user['uid'], "unread": 1})

        for n in unread_notices:
            self.db.notice.update({"_id": ObjectId(n["_id"])}, {"$set": {"unread": 0}})
        # for m in unread_messages:
        #     self.db.message.update({"_id": ObjectId(m["_id"])}, {"$set": {"unread": 0}})

        total_unread = unread_notices.count() + unread_messages.count()
        self.db.user.update({"uid": self.user['uid']}, {"$set": {"unread": total_unread}})
        user = self.db.user.find_one({"uid": self.user['uid']})

        def user_info(uid):
            self.db.user.find_one({'uid': uid})

        if type == 'message':
            self.settings['show_im'] = True
            messages = self.db.message.find({"receiver_id": self.user['uid']}).skip(per * (current_page - 1)).sort(
                "_id", pymongo.DESCENDING).limit(5)
            notices = {}
            template = 'user/user-message-center.html'
        else:
            notices = self.db.notice.find({"uid": self.user['uid']}).skip(per * (current_page - 1)).sort(
                "_id", pymongo.DESCENDING).limit(5)
            # for i in notices:
            #     print i
            messages = {}
            template = 'user/user-notice-center.html'
        self.render(template, myuser=user, notices=notices, unread_notices=unread_notices,
                    messages=messages, unread_messages=unread_messages, user_info=user_info, start_index=start_index,
                    next_page=next_page, current_page=current_page, notice_counts=notice_counts,
                    messages_counts=messages_counts, type=type, account_tab=10)


class DelNoticeHandler(BaseHandler):
    """删除系统通知"""

    def post(self):
        notice_ids = list(self.request.arguments['ids[]'])
        for n in notice_ids:
            self.db.notice.remove({"_id": ObjectId(n), "uid": self.user['uid']})
        self.write(json.dumps({"status": "ok", "msg": u"已删除"}))
