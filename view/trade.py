# encoding: utf-8
import json
import os
from urllib import urlencode
import uuid
import math
from passlib.handlers.pbkdf2 import pbkdf2_sha512
import time
from pymongo import DESCENDING, ASCENDING
import pymongo

from BaseHandler import BaseHandler


class Zhuanjihuobi(BaseHandler):
    """转激活币"""

    @BaseHandler.authenticated
    @BaseHandler.is_active
    def get(self):
        self.render("trade/zhuanjihuobi.html", account_tab=15, myuser=self.user)

    @BaseHandler.authenticated
    @BaseHandler.is_active
    def post(self):
        uid = self.get_argument("uid", "")
        out_money = int(self.get_argument("money", 0))
        try:
            my_money = int(self.user.get("money", 0))
        except ValueError:
            my_money = 0

        if my_money <= 0 or my_money - out_money < 0:
            # 金额一定要小于用户余额
            self.render("ok.html", url="/trade/zhuanjihuobi", tip="您的激活币不足，请联系上级充值")
            return
        member = self.db.user.find_one({"uid": uid})

        if member:
            # trade_log_id自增1
            last_trade_log = self.db.trade_log.find().sort("id", pymongo.DESCENDING).limit(1)
            if last_trade_log.count() > 0:
                lastone = dict()
                for item in last_trade_log:
                    lastone = item
                trade_log_id = int(lastone.get('id', 0)) + 1
            else:
                trade_log_id = 1

            # 更新发放激活币的用户的余额
            admin_money = my_money - out_money
            self.db.user.update({"uid": self.user.get("uid")}, {"$set": {"money": admin_money}})
            self.db.user.update({"uid": uid}, {"$inc": {"money": out_money}})

            # 转账记录
            self.db.trade_log.insert({
                "id": trade_log_id,
                "uid": self.user.get("uid"),
                "type": "transfer",
                "mid": uid, "money": out_money,
                "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))})
            # TODO 激活币收入记录

            tip = "激活币转账成功"

            self.render("ok.html", url="/trade/zhuanjihuobi", tip=tip)
        else:
            self.render("ok.html", url="/trade/zhuanjihuobi", tip="该会员不存在")


class Zhuanjinbi(BaseHandler):
    """转金币"""

    @BaseHandler.authenticated
    @BaseHandler.is_active
    def get(self):
        self.render("trade/zhuanjinbi.html", account_tab=16, myuser=self.user)

    @BaseHandler.authenticated
    @BaseHandler.is_active
    def post(self):
        uid = self.get_argument("uid", None)
        out_money = int(self.get_argument("jinbi", 0))
        try:
            my_money = int(self.user.get("jinbi", 0))
        except ValueError:
            my_money = 0

        if my_money <= 0 or my_money - out_money < 0:
            # 金额一定要小于用户余额
            self.render("ok.html", url="/trade/zhuanjinbi", tip="您的金币不足，请联系上级充值")
            return
        member = self.db.user.find_one({"uid": uid})

        if member:
            # trade_log_id自增1
            last_trade_log = self.db.jinbi.find().sort("id", pymongo.DESCENDING).limit(1)
            if last_trade_log.count() > 0:
                lastone = dict()
                for item in last_trade_log:
                    lastone = item
                trade_log_id = int(lastone.get('id', 0)) + 1
            else:
                trade_log_id = 1

            # 更新发放金币的用户的金币余额
            admin_jinbi = my_money - out_money
            now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
            self.db.user.update({"uid": self.user.get("uid")}, {"$set": {"jinbi": admin_jinbi}})

            # 更新收到金币的用户的金币余额
            new_jinbi = member.get("jinbi", 0)
            print out_money
            self.db.user.update({"uid": uid}, {"$inc": {"jinbi": out_money}})

            # 转账记录
            self.db.jinbi.insert({
                "id": trade_log_id,
                "type": "transfer",
                "uid": self.user.get("uid"),
                "mid": uid, "money": out_money,
                "time": now_time})

            # 转入记录
            self.db.jinbi.insert({
                "id": trade_log_id + 1,
                "type": "in",
                "uid": uid,
                "mid": self.user.get("uid"),
                "money": out_money,
                "time": now_time})
            tip = "金币转账成功"

            self.render("ok.html", url="/trade/zhuanjinbi", tip=tip)
        else:
            self.render("ok.html", url="/trade/zhuanjinbi", tip="该会员不存在")


class GetCrash(BaseHandler):
    """提现"""

    @BaseHandler.authenticated
    @BaseHandler.is_active
    def get(self):
        self.render("trade/maijb.html", account_tab=17, myuser=self.user)

    @BaseHandler.authenticated
    @BaseHandler.is_active
    def post(self):
        account = self.get_argument("account", "")
        alipay_name = self.get_argument("alipay_name", "")
        account_type = self.get_argument("account_type", "")
        crash_money = self.get_argument("money", 0)
        try:
            crash_money = int(crash_money)
        except ValueError:
            crash_money = 0
        if crash_money <= 0:
            return self.render("ok.html", url="/trade/maijb", tip="请输入合法的数字金额")
        print "crash_money,", crash_money
        # trade_log_id自增1
        last_trade_log = self.db.jinbi.find().sort("id", pymongo.DESCENDING).limit(1)
        if last_trade_log.count() > 0:
            lastone = dict()
            for item in last_trade_log:
                lastone = item
            trade_log_id = int(lastone.get('id', 0)) + 1
        else:
            trade_log_id = 1

        # 更新发放金币的用户的余额
        my_money = int(self.user.get("jinbi", 0))
        if my_money - crash_money < 0:
            return self.render("ok.html", url="/trade/maijb", tip="提现金额大于金币余额")
        new_money = my_money - crash_money
        self.db.user.update({"uid": self.user.get("uid")}, {"$set": {"jinbi": new_money}})
        self.db.jinbi.insert({
            "id": trade_log_id,
            "type": "get_crash",
            "uid": self.user.get("uid"),
            "money": crash_money,
            "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))})
        # trade_log_id自增1
        last_trade_log = self.db.apply_crash.find().sort("id", pymongo.DESCENDING).limit(1)
        if last_trade_log.count() > 0:
            lastone = dict()
            for item in last_trade_log:
                lastone = item
            apply_id = int(lastone.get('id', 0)) + 1
        else:
            apply_id = 1

        # 写入提现记录表
        self.db.apply_crash.insert({
            "id": apply_id,
            "uid": self.user.get("uid"),
            "status": "submit",
            "money": crash_money,
            "account": {"account": account, "type": account_type},
            "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))})

        # self.db.user.update({"uid": self.user.get("uid")},
        #                     {"$set": {"alipay": account}})

        tip = "提现申请已提交"

        self.render("ok.html", url="/trade/jbdingdan", tip=tip)


class GetCrashLog(BaseHandler):
    """提现记录"""

    @BaseHandler.authenticated
    @BaseHandler.is_active
    def get(self):
        record = self.db.apply_crash.find({"uid": self.user.get("uid")})
        self.render("trade/jbdingdan.html", account_tab=18, record=record, myuser=self.user)


class JinBiPaiMai(BaseHandler):
    """金币拍卖"""

    @BaseHandler.authenticated
    @BaseHandler.is_active
    def get(self):
        record = self.db.jinbi.find({"type": "guadan", "uid": {"$ne": self.user.get("uid")}, "status": "waiting"}).sort(
            "id", pymongo.DESCENDING).limit(50)
        self.render("trade/jinbi_guadan.html", account_tab=12, record=record, myuser=self.user)


class JinBiGoumai(BaseHandler):
    """金币购买记录"""

    @BaseHandler.authenticated
    @BaseHandler.is_active
    def get(self):
        record = self.db.jinbi.find({"pay_uid": self.user.get('uid')}).sort("id", pymongo.DESCENDING)

        def alipay_info(uid):
            info = self.db.user.find_one({"uid": uid})
            if not info:
                return {}
            else:
                return info.get('alipay')

        self.render("trade/jinbi_mai.html", account_tab=13, record=record, alipay_info=alipay_info, myuser=self.user)


class JinBiMai(BaseHandler):
    """金币卖出记录"""

    @BaseHandler.authenticated
    @BaseHandler.is_active
    def get(self):
        mai_status = {"confirm": "已抢购，等待确认付款", "paid": "已付款", "complete": "已完成"}
        record = self.db.jinbi.find(
            {"type": "guadan", "status": {"$in": ['paid', 'complete']}, "uid": self.user.get('uid')}).sort("id",
                                                                                                           pymongo.DESCENDING)
        alipay_info = self.db.user.find_one({"uid": self.user.get("uid")}).get("alipay")
        self.render("trade/jinbi_mai2.html", account_tab=14, mai_status=mai_status, record=record,
                    alipay_info=alipay_info, myuser=self.user)


class JinBiGuadan(BaseHandler):
    """金币挂单"""

    @BaseHandler.authenticated
    @BaseHandler.is_active
    def get(self):
        if not self.user.get("alipay"):
            self.render("ok.html", url="/account/info_setting", tip="请先完善个人信息")
            return

        self.render("trade/woyao_guadan.html", account_tab=16, myuser=self.user)

    @BaseHandler.authenticated
    @BaseHandler.is_active
    def post(self):
        out_jinbi = int(self.get_argument("jinbi", 0))
        try:
            my_jinbi = int(self.user.get("jinbi", 0))
        except ValueError:
            my_jinbi = 0
        if my_jinbi <= 0 or my_jinbi - out_jinbi < 0:
            # 金额一定要小于用户余额
            self.render("ok.html", url="/trade/woyao_guadan", tip="您的金币不足，请联系上级充值")
            return

        # trade_log_id自增1
        last_trade_log = self.db.jinbi.find().sort("id", pymongo.DESCENDING).limit(1)
        if last_trade_log.count() > 0:
            lastone = dict()
            for item in last_trade_log:
                lastone = item
            trade_log_id = int(lastone.get('id', 0)) + 1
        else:
            trade_log_id = 1

        # 更新用户的金币余额
        admin_money = my_jinbi - out_jinbi
        self.db.user.update({"uid": self.user.get("uid")}, {"$set": {"jinbi": admin_money}})

        # 挂单记录
        self.db.jinbi.insert({
            "id": trade_log_id,
            "type": "guadan",
            "uid": self.user.get("uid"),
            "money": out_jinbi,
            "status": "waiting",
            "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))})
        tip = "挂单成功"

        self.render("ok.html", url="/trade/jinbi_guadan", tip=tip)


class JinBiQianggou(BaseHandler):
    """金币抢购"""

    @BaseHandler.authenticated
    @BaseHandler.is_active
    def get(self):
        id = int(self.get_argument("id", 0))
        print id
        record = self.db.jinbi.find_one({"id": id})
        if not record:
            self.render("ok.html", url="/trade/jinbi_guadan", tip="该单号id不存在")
            return
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        self.db.jinbi.update({"id": id},
                             {"$set": {"pay_uid": self.user.get("uid"), "status": "confirm",
                                       "pay_time": current_time}})
        self.redirect('/trade/jinbi_mai')


class JinBiQuerenPay(BaseHandler):
    """金币抢购确认付款"""

    @BaseHandler.authenticated
    @BaseHandler.is_active
    def get(self):
        if not self.user.get("alipay"):
            self.render("ok.html", url="/account/info_setting", tip="请先完善个人信息")
            return
        try:
            id = int(self.get_argument("id", 0))
        except Exception, e:
            self.render("ok.html", url="/trade/jinbi_guadan", tip="该单号id不存在")
            return
        record = self.db.jinbi.find_one({"id": id})
        uid = record.get("uid")
        aliplay_info = self.db.user.find_one({"uid": uid}).get("alipay")

        self.render("trade/jinbi_qianggou.html", account_tab=16, record=record, aliplay_info=aliplay_info,
                    myuser=self.user)

    @BaseHandler.authenticated
    @BaseHandler.is_active
    def post(self):
        id = int(self.get_argument("id", 0))
        pay_image = self.get_argument("pay_image", "")
        print id, pay_image
        record = self.db.jinbi.find_one({"id": id})
        if not record:
            self.render("ok.html", url="/trade/jinbi_guadan", tip="该单号id不存在")
            return
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        self.db.jinbi.update({"id": id},
                             {"$set": {"status": "paid", "pay_uid": self.user.get("uid"), "pay_image": pay_image,
                                       "pay_time": current_time}})
        self.redirect('/trade/jinbi_mai')


class JinbiQianggouCancel(BaseHandler):
    """取消金币抢购"""

    @BaseHandler.authenticated
    @BaseHandler.is_active
    def get(self):
        id = int(self.get_argument("id", 0))
        self.db.jinbi.update({"id": id}, {"$set": {"status": "waiting"},
                                          "$unset": {"pay_image": "", "pay_time": "", "pay_uid": ""}})
        # 扣除2金币
        self.db.user.update({"uid": self.user.get("uid")}, {"$inc": {"jinbi": -2}})
        self.redirect('/trade/jinbi_mai')


class JinBiConfirmPaid(BaseHandler):
    """金币抢购，确认收款"""

    @BaseHandler.authenticated
    @BaseHandler.is_active
    def get(self):
        id = int(self.get_argument("id", 0))
        record = self.db.jinbi.find_one({"id": id})
        if not record:
            self.render("ok.html", url="/trade/jinbi_mai2", tip="该单号id不存在")
            return
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        # TODO 标记为已完成
        self.db.jinbi.update({"id": id},
                             {"$set": {"status": "complete", "confirm_time": current_time}})

        # TODO 抢购人将获得对应数额金币
        # trade_log_id自增1
        last_trade_log = self.db.jinbi.find().sort("id", pymongo.DESCENDING).limit(1)
        if last_trade_log.count() > 0:
            lastone = dict()
            for item in last_trade_log:
                lastone = item
            trade_log_id = int(lastone.get('id', 0)) + 1
        else:
            trade_log_id = 1

        buyer_uid = record.get("pay_uid")
        buyer_jinbi = self.db.user.find_one({"uid": buyer_uid}).get("jinbi")
        money = record.get("money")

        # 更新买金币的人的金币余额
        new_jinbi = buyer_jinbi + money
        self.db.user.update({"uid": buyer_uid}, {"$set": {"jinbi": new_jinbi}})

        # 生成金币记录
        self.db.jinbi.insert({
            "id": trade_log_id,
            "type": "qianggou",
            "uid": buyer_uid,
            "gid": id,
            "seller": self.user.get("uid"),
            "money": money,
            "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))})

        self.redirect('/trade/jinbi_mai2')
