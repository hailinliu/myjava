# encoding: utf-8
import json
import os
from urllib import urlencode
import uuid
import math
from passlib.handlers.pbkdf2 import pbkdf2_sha512
import time
from pymongo import DESCENDING, ASCENDING

from BaseHandler import BaseHandler
from utils.uploadsets import process_question


class LogoutHandler(BaseHandler):
    """注销"""

    def get(self):
        self.post()

    def post(self):
        self.end_session()
        self.redirect('/login')


class AccountActivate(BaseHandler):
    """账户激活"""

    def get(self):
        if self.get_argument("page", None) in ["", None]:
            current_page = 1
        else:
            current_page = int(self.get_argument("page"))
        members = self.db.user.find({"admin": self.user.get("uid")}).sort("active_time", ASCENDING)
        per = 10.0
        print members.count() / per
        print math.ceil(members.count() / per)
        pages = int(math.ceil(members.count() / per))
        members = members.skip(int(per) * (current_page - 1)).limit(int(per))
        counts = members.count()

        self.render("account/member_activate.html", current_tab=1, members=members, current_page=current_page,
                    counts=counts, pages=pages, myuser=self.user)

    def post(self):
        uid = self.get_argument("uid", None)
        reid = self.get_argument("reid", None)
        info = {}
        try:
            my_money = int(self.user.get("money", 0))
        except ValueError:
            my_money = 0

        if my_money < 100:
            # 转账金额一定要小于用户余额
            self.render("ok.html", url="/account/activate", tip="您的激活币不足，请联系上级充值")
            return
        member = self.db.user.find_one({"uid": uid})

        if member:
            if not member.get("is_check"):
                # TODO 未激活-->激活则从用户余额扣除100
                # 更新发放激活币的用户的余额
                admin_money = my_money - 100
                self.db.user.update({"uid": self.user.get("uid")}, {"$set": {"money": admin_money}})
                tip = "激活成功"
                info.update({"is_check": True, 'active_time': time.strftime("%Y-%m-%d %H:%M:%S",
                                                                            time.localtime(time.time()))})
                self.db.user.update({"uid": uid}, {"$set": info})
                # 转账记录
                self.db.trade_log.insert({
                    "uid": self.user.get("uid"),
                    "mid": uid, "money": 100,
                    "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))})
            else:
                tip = "该会员已激活，无需再激活"
            self.render("ok.html", url="/account/activate", tip=tip)
        else:
            self.render("ok.html", url="/account/activate", tip="该会员不存在")


class AccountInfoSetting(BaseHandler):
    """更新资料"""

    @BaseHandler.check_pwd_protect
    @BaseHandler.is_check
    def get(self):
        error = ""
        self.render("account/info_setting.html", current_tab=1, error=error, myuser=self.user)

    @BaseHandler.is_check
    def post(self):
        datas = self.request.arguments
        if None in [self.user.get("question"), self.user.get("answer")]:
            self.render("ok.html", url="/account/pwd_protect", tip="请先设置密保然后修改资料")
        info = {}
        passquestion1 = self.get_argument("passquestion1")
        passanswer1 = self.get_argument("passanswer1")
        wechat = self.get_argument("wechat", "")
        alipay = self.get_argument("alipay", "")
        bankname = self.get_argument("bankname", "")  # 银行卡类型 哪家银行
        BankCard = self.get_argument("BankCard", "")  # 银行卡卡号
        BankUserName = self.get_argument("BankUserName", "")  # 银行卡用户名
        BankAddress = self.get_argument("BankAddress", "")  # 银行卡地址
        # print self.user.get("question"),self.user.get("answer")
        # TODO 必须先验证密保才能修改
        if passquestion1 == self.user.get("question") and passanswer1 == self.user.get("answer"):
            # info.update({"question": passquestion1, "answer": passanswer1})
            pass
            # self.db.user.update({"uid": self.user.get("uid")}, {"$set": info})
        else:
            self.render("ok.html", url="/account/info_setting", tip="密保问题或答案不正确")
        if wechat == "" and alipay == "":
            self.render("ok.html", url="/account/info_setting", tip="支付宝或微信号至少填写一个")
        else:
            info.update({"wechat": wechat, "alipay": alipay})
            self.db.user.update({"uid": self.user.get("uid")}, {"$set": info})

        if "" in [BankCard, bankname, BankUserName, BankAddress]:
            self.render("ok.html", url="/account/info_setting", tip="请完善银行卡信息")
        else:
            info.update(
                {"bank": {"name": bankname, "card": BankCard, "user_name": BankUserName, "address": BankAddress}})
            print info
            self.db.user.update({"uid": self.user.get("uid")}, {"$set": info})
            self.render("ok.html", url="/account/info_setting", tip="资料修改成功")
        self.render("account/info_setting.html", current_tab=1, myuser=self.user)




class AccountPwdUpdate(BaseHandler):
    """密码更新"""

    @BaseHandler.is_check
    def get(self):
        error = ""
        self.render("account/pwd_update.html", current_tab=1, error=error, myuser=self.user)

    @BaseHandler.is_check
    def post(self):
        datas = self.request.arguments
        formType = self.get_argument("form_type")
        if formType == 'form1':
            opwd = self.get_argument("password1")
            # print opwd
            npwd = self.get_argument("npassword1")
            # 旧密码验证
            print pbkdf2_sha512.verify(opwd, self.user['pwd'])
            if not self.application.auth.log_in(self.user['uid'], opwd):
                self.render("ok.html", url="/account/pwd_update", tip="旧密码不正确")
                # 新密码写入
            if not self.application.auth.changepwd(self.user['uid'], npwd):
                self.render("ok.html", url="/account/pwd_update", tip="密码修改失败")
            else:
                self.render("ok.html", url="/account/pwd_update", tip="密码已修改")
        elif formType == 'form2':

            old_safe_pwd = self.get_argument("password2")
            new_safe_pwd = self.get_argument("npassword2")
            print old_safe_pwd
            # 旧密码验证
            print "form2"
            if old_safe_pwd != self.user.get("safe_pwd"):
                self.render("ok.html", url="/account/pwd_update", tip="旧安全密码不正确")
            # 新密码写入
            self.db.user.update({"uid": self.user.get("uid")}, {"$set": {"safe_pwd": new_safe_pwd}})
            self.render("ok.html", url="/account/pwd_update", tip="二级密码已修改")
        else:
            pass

        self.render("account/pwd_update.html", current_tab=1, myuser=self.user)


class AccountPwdProtect(BaseHandler):
    """密保设置"""

    def get(self):
        error = ""
        self.render("account/pwd_protect.html", current_tab=1, error=error, myuser=self.user)

    @BaseHandler.is_check
    def post(self):
        datas = self.request.arguments
        # print datas
        # 旧密保
        question1 = self.get_argument("question1", None)
        answer1 = self.get_argument("answer1", None)
        # print self.user.get("answer")
        # print self.user.get("question")
        # print answer1 ==self.user.get("answer")
        # print question1 ==self.user.get("question")
        # 新密保
        question2 = self.get_argument("question2", None)
        answer2 = self.get_argument("answer2", None)
        if answer2 in ["", None]:
            self.render("ok.html", url="/account/pwd_protect", tip="密保答案不能为空")

        user_pwd_question = self.user.get("question")
        user_pwd_answer = self.user.get("answer")
        # 当用户没有设置密保的时候
        if None in [user_pwd_question, user_pwd_answer]:
            self.db.user.update({"uid": self.user.get("uid")}, {"$set": {"question": question2, "answer": answer2}})
            self.render("ok.html", url="/account/pwd_protect", tip="密保修改成功")
        else:
            if question1 == user_pwd_question and answer1 == user_pwd_answer:
                self.db.user.update({"uid": self.user.get("uid")}, {"$set": {"question": question2, "answer": answer2}})
                self.render("ok.html", url="/account/pwd_protect", tip="密保修改成功")
            else:
                self.render("ok.html", url="/account/pwd_protect", tip="旧密保不正确")
        self.render("account/pwd_protect.html", current_tab=1, myuser=self.user)


class SafePwdCheck(BaseHandler):
    """安全密码校验"""

    @BaseHandler.authenticated
    def get(self):
        error = ""
        self.render("account/verify_safe_pwd.html", current_tab=1, next_url="", error=error, myuser=self.user)

    @BaseHandler.authenticated
    def post(self):
        data = self.request.arguments
        pwd = self.get_argument("password2", "")
        next_url = data.get("next")[0]
        if pwd != self.user.get("safe_pwd"):
            error = "二级密码错误，请重新输入"
            self.render("account/verify_safe_pwd.html", current_tab=1, next_url=next_url, error=error, yuser=self.user)
        else:
            self.session['safe_pwd'] = pwd
            self.set_secure_cookie("safe_pwd", pwd)
        self.redirect(next_url)


class AccountAwardDetail(BaseHandler):
    """奖金记录"""

    @BaseHandler.authenticated
    def get(self):
        reward_type = self.settings['reward_type']
        records = self.db.reward_record.find({"uid": self.user.get("uid")})
        self.render("account/award_record.html", current_tab=2, reward_type=reward_type, records=records,
                    myuser=self.user)


class AccountMembers(BaseHandler):
    """直属会员"""

    @BaseHandler.authenticated
    def get(self):
        if self.get_argument("page", None) in ["", None]:
            current_page = 1
        else:
            current_page = int(self.get_argument("page"))
        members = self.db.user.find({"admin": self.user.get("uid")})
        per = 10.0
        pages = int(math.ceil(members.count() / per))
        members = members.skip(int(per) * (current_page - 1)).limit(int(per))
        counts = members.count()

        self.render("account/members.html", current_tab=2, members=members, current_page=current_page, pages=pages,
                    counts=counts, myuser=self.user)
