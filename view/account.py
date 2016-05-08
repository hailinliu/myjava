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
from utils.uploadsets import process_question


class LogoutHandler(BaseHandler):
    """注销"""

    def get(self):
        self.post()

    def post(self):
        self.end_session()
        self.redirect('/login')


class TuijianJg(BaseHandler):
    """推荐结构"""

    @BaseHandler.authenticated
    @BaseHandler.is_active
    def get(self):

        members = self.db.user.find({"admin": str(self.user.get("uid"))})

        def member_count(uid):
            return self.db.user.find({"admin": str(uid)}).count()

        def sub_members(uid):
            users = self.db.user.find({"admin": str(uid)}, {"_id": 0})
            if users.count() == 0:
                return {}
            else:
                return users

        def test_tree(uid):
            base_template = """

             <ul id="wenjianshu" class="ztree">
                                {%for m in members %}
                                <li class="level0" tabindex="0" hidefocus="true" treenode=""><span
                                         title="" class="button level0 switch root_docu"
                                        treenode_switch=""></span>
                                    <a  class="level0" treenode_a="" onclick="" target="_blank" style=""
                                                                     title="">
                                        <span title="" treenode_ico="" class="button ico_docu"
                                        style="background:url(/ui/zTree_v3/css/zTreeStyle/img/diy/1_open.png) 0 0 no-repeat;"></span>
                                        <span class="node_name">[{{member_count(m.get('uid'))}}] {{m.get('uid')}}
                                    [{%if m.get('is_active')%}已激活{%else%}未激活{%end%}]
                                    [VIP{%if m.get('level')!=0%}{{m.get('level')}}{%else%}{%end%}]
                                </span></a>

                                    {%end%}
                                </li>
                                {%end%}
                            </ul>
            """

            ul = """ <ul  class="ztree">"""
            for m in members:
                mid = m.get('uid')
                li = """
                <li class="level0" tabindex="0" hidefocus="true" treenode=""><span
                                         title="" class="button level0 switch root_docu"
                                        treenode_switch=""></span>
                                    <a  class="level0" treenode_a="" onclick="" target="_blank" style=""
                                                                     title="">
                                        <span title="" treenode_ico="" class="button ico_docu"
                                        style="background:url(/ui/z]Tree_v3/css/zTreeStyle/img/diy/1_open.png) 0 0 no-repeat;"></span>
                                        <span class="node_name">[{0} {1}

                """.format(member_count(m.get('uid')), m.get('uid'))
                if m.get('is_active'):
                    li += """[已激活]"""
                else:
                    li += """[未激活]"""
                li += """ [VIP{0}] """.format(str(m.get('level', "")))

                li += "</span></a>"
                while member_count(mid) > 0:
                    sub_ul = """"""
                    if member_count(m.get('uid')):
                        sub_member = sub_members(m.get('uid'))
                        for mm in sub_member:
                            li += """"""
                li += "</li>"
                ul += li
            ul += " </ul>"

        self.render("account/tjjg.html", member_count=member_count, members=members, sub_members=sub_members,
                    myuser=self.user,
                    account_tab=4)


class Zhitui(BaseHandler):
    """直推"""

    @BaseHandler.authenticated
    @BaseHandler.is_active
    def get(self):
        per = 10
        records = self.db.user.find({"admin": str(self.user.get("uid"))})
        counts = records.count()
        current_page = int(self.get_argument("p", 1))
        pages = int(round(counts / 10.0))
        if pages == 0:
            pages = 1
        if current_page <= 1:
            prev_page = 1
            next_page = 1
        else:
            prev_page = current_page - 1
            next_page = current_page + 1
        records = records.skip(per * (current_page - 1)).sort("_id", pymongo.DESCENDING).limit(10)
        self.render("account/zhitui.html", account_tab=5, current_page=current_page, counts=counts,
                    records=records, pages=pages, prev_page=prev_page, next_page=next_page,
                    myuser=self.user)


class Jihuo(BaseHandler):
    """激活账号"""

    @BaseHandler.authenticated
    @BaseHandler.is_active
    def get(self):
        self.render("account/jihuo.html", account_tab=6, myuser=self.user)

    @BaseHandler.authenticated
    @BaseHandler.is_active
    def post(self):
        uid = self.get_argument("uid", None)
        info = {}
        try:
            my_money = int(self.user.get("money", 0))
        except ValueError:
            my_money = 0

        if my_money < 50:
            # 金额一定要小于用户余额
            self.render("ok.html", url="/account/jihuo", tip="您的激活币不足，请联系上级充值")
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

            if not member.get("is_active"):
                # TODO 未激活-->激活则从用户余额扣除50
                # 更新发放激活币的用户的余额
                admin_money = my_money - 50
                self.db.user.update({"uid": self.user.get("uid")}, {"$set": {"money": admin_money}})
                tip = "激活成功"
                info.update({"is_active": True, 'active_time': time.strftime("%Y-%m-%d %H:%M:%S",
                                                                             time.localtime(time.time()))})
                self.db.user.update({"uid": uid}, {"$set": info})
                # 转账记录
                self.db.trade_log.insert({
                    "type": "jihuo",
                    "id": trade_log_id,
                    "uid": self.user.get("uid"),
                    "mid": uid, "money": 50,
                    "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))})
                now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))

                # TODO 更新上级代理的金币  从系统配置中
                setting = self.db.setting.find_one({"type": 1})
                if not setting:
                    gain = 18
                else:
                    gain = setting.get("recommend_award", 18)
                    # trade_log_id自增1
                last_trade_log = self.db.jinbi.find().sort("id", pymongo.DESCENDING).limit(1)

                if last_trade_log.count() > 0:
                    lastone = dict()
                    for item in last_trade_log:
                        lastone = item
                    trade_log_id = int(lastone.get('id', 0)) + 1
                else:
                    trade_log_id = 1
                self.db.user.update({"uid": self.user.get("uid")}, {
                    "$set": {"jinbi": self.user.get("jinbi", 0) + 18}})

                self.db.jinbi.insert(
                    {"id": trade_log_id, "type": 'tuijian', "uid": self.user.get("uid"), "rid": uid, 'money': gain,
                     "time": now_time})
            else:
                tip = "该会员已激活，无需再激活"
            self.render("ok.html", url="/account/jihuo", tip=tip)
        else:
            self.render("ok.html", url="/account/jihuo", tip="该会员不存在")


class JihuoRecord(BaseHandler):
    """激活记录"""

    @BaseHandler.authenticated
    @BaseHandler.is_active
    def get(self):
        record = self.db.trade_log.find({"uid": self.user.get("uid"), "type": "jihuo"})
        self.render("account/jihuojl.html", account_tab=7, record=record, myuser=self.user)


class JiHuobiLog(BaseHandler):
    """激活币收入"""

    @BaseHandler.authenticated
    @BaseHandler.is_active
    def get(self):
        per = 10
        records = self.db.trade_log.find({"mid": self.user.get("uid"), "type": "transfer"})
        total = 0
        counts = records.count()
        records_result = self.db.trade_log.aggregate(
            [{"$match": {"mid": self.user.get("uid"), "type": "transfer"}},
             {"$group": {'_id': "", 'sum': {'$sum': '$money'}}}])['result']
        if len(records_result) > 0:
            total = records_result[0]['sum']
        current_page = int(self.get_argument("p", 1))
        pages = int(round(counts / 10.0))
        if pages == 0:
            pages = 1
        if current_page <= 1:
            prev_page = 1
            next_page = 1
        else:
            prev_page = current_page - 1
            next_page = current_page + 1
        records = records.skip(per * (current_page - 1)).sort("_id", pymongo.DESCENDING).limit(10)
        self.render("finance/jihuobi_log.html", total=total, account_tab=8, current_page=current_page, counts=counts,
                    records=records, pages=pages, prev_page=prev_page, next_page=next_page,
                    myuser=self.user)


class JiHuobiLog2(BaseHandler):
    """激活币支出"""

    @BaseHandler.authenticated
    @BaseHandler.is_active
    def get(self):
        type_dict = {"jihuo": "账户激活", "transfer": "激活币转账"}
        type_list = ['jihuo', 'transfer']
        total_consume = 0
        per = 10
        records = self.db.trade_log.find({"type": {"$in": type_list}, "uid": self.user.get("uid")})
        records_result = self.db.trade_log.aggregate(
            [{"$match": {"uid": self.user.get("uid"), "type": {"$in": type_list}}},
             {"$group": {'_id': "", 'sum': {'$sum': '$money'}}}])['result']
        if len(records_result) > 0:
            total_consume = records_result[0]['sum']
        counts = records.count()
        current_page = int(self.get_argument("p", 1))
        pages = int(round(counts / 10.0))
        if pages == 0:
            pages = 1
        if current_page <= 1:
            prev_page = 1
            next_page = 1
        else:
            prev_page = current_page - 1
            next_page = current_page + 1
        records = records.skip(per * (current_page - 1)).sort("_id", pymongo.DESCENDING).limit(10)
        self.render("finance/jihuobi_log2.html", account_tab=9, records=records, total_consume=total_consume,
                    counts=counts, pages=pages,
                    current_page=current_page, prev_page=prev_page, next_page=next_page, type_dict=type_dict,
                    myuser=self.user)


class JinBiLog(BaseHandler):
    """金币收入"""

    @BaseHandler.authenticated
    @BaseHandler.is_active
    def get(self):
        # 宠物生产,pet_id
        per = 10
        total_consume = 0
        type_list = ["in", "pet_produce", "qianggou", "tuijian"]
        tip_dict = {"in": "金币转账", "pet_produce": "宠物生产", "qianggou": "抢购金币", "tuijian": "推荐奖"}
        records = self.db.jinbi.find({"type": {"$in": type_list}, "uid": self.user.get("uid")})
        records_result = self.db.jinbi.aggregate(
            [{"$match": {"uid": self.user.get("uid"), "type": {"$in": type_list}}},
             {"$group": {'_id': "", 'sum': {'$sum': '$money'}}}])['result']
        if len(records_result) > 0:
            total_consume = records_result[0]['sum']
        counts = records.count()
        current_page = int(self.get_argument("p", 1))
        pages = int(round(counts / 10.0))
        if pages == 0:
            pages = 1
        if current_page <= 1:
            prev_page = 1
            next_page = 1
        else:
            prev_page = current_page - 1
            next_page = current_page + 1

        records = records.skip(per * (current_page - 1)).sort("_id", pymongo.DESCENDING).limit(10)

        self.render("finance/jinbi_log.html", account_tab=10, records=records, counts=counts, tip_dict=tip_dict,
                    current_page=current_page, pages=pages, total_consume=total_consume, prev_page=prev_page,
                    next_page=next_page, myuser=self.user)


class JinBiLog2(BaseHandler):
    """金币支出"""
    # status
    # submit:已提交,等待发货
    # shipped:已发货

    @BaseHandler.authenticated
    @BaseHandler.is_active
    def get(self):
        per = 10
        total_consume = 0
        type_list = ["transfer", "buy_pet", "guadan", "get_crash", "draw"]
        tip_dict = {"transfer": "金币转账", "buy_pet": "宠物消费", "guadan": "金币拍卖", "get_crash": "金币提现", "draw": "抽奖消费"}
        records = self.db.jinbi.find({"type": {"$in": type_list}, "uid": self.user.get("uid")})
        records_result = self.db.jinbi.aggregate(
            [{"$match": {"uid": self.user.get("uid"), "type": {"$in": type_list}}},
             {"$group": {'_id': "", 'sum': {'$sum': '$money'}}}])['result']
        if len(records_result) > 0:
            total_consume = records_result[0]['sum']
        counts = records.count()
        current_page = int(self.get_argument("p", 1))
        pages = int(round(counts / 10.0))
        if pages == 0:
            pages = 1
        if current_page <= 1:
            prev_page = 1
            next_page = 1
        else:
            prev_page = current_page - 1
            next_page = current_page + 1

        records = records.skip(per * (current_page - 1)).sort("_id", pymongo.DESCENDING).limit(10)

        self.render("finance/jinbi_log2.html", account_tab=11, records=records, counts=counts, tip_dict=tip_dict,
                    current_page=current_page, pages=pages, total_consume=total_consume, prev_page=prev_page,
                    next_page=next_page, myuser=self.user)


class UserAddressSetting(BaseHandler):
    """收货地址设置"""

    @BaseHandler.authenticated
    @BaseHandler.is_active
    def get(self):
        self.render("account/address_info.html", account_tab=20, myuser=self.user)

    @BaseHandler.authenticated
    @BaseHandler.is_active
    def post(self):
        city = self.get_argument("city", "")
        address = self.get_argument("address", "")
        username = self.get_argument("username", "")
        phone = self.get_argument("phone", "")
        if "" in [address, phone]:
            self.render("ok.html", url="/account/address_setting", tip="请填写完整信息")
        address_info = {}
        address_info.update({"province_city": city, "address": address, "username": username, "phone": phone})
        self.db.user.update({"uid": self.user.get('uid')}, {"$set": {"address_info": address_info}})
        self.redirect('/account/address_setting')


class UserAlipaySetting(BaseHandler):
    """支付宝信息设置"""

    @BaseHandler.authenticated
    @BaseHandler.is_active
    def get(self):
        self.render("account/alipay_setting.html", account_tab=1, myuser=self.user)

    @BaseHandler.authenticated
    @BaseHandler.is_active
    def post(self):
        alipay_account = self.get_argument("alipay_account", "")
        alipay_name = self.get_argument("alipay_name", "")
        if "" in [alipay_name, alipay_account]:
            self.render("ok.html", url="/account/alipay_setting", tip="请填写完整信息")
        alipay_info = {}
        alipay_info.update({"name": alipay_name, "account": alipay_account})
        self.db.user.update({"uid": self.user.get('uid')}, {"$set": {"alipay": alipay_info}})
        self.redirect('/trade/jinbi_guadan')


class MyOrder(BaseHandler):
    """我的订单"""

    @BaseHandler.authenticated
    @BaseHandler.is_active
    def get(self):

        per = 10
        total_consume = 0
        order_status = {"submit": "待发货", "shipped": "已发货"}
        records = self.db.product_order.find({"uid": self.user.get("uid")})
        records_result = self.db.product_order.aggregate(
            [{"$match": {"uid": self.user.get("uid")}}, {"$group": {'_id': "", 'sum': {'$sum': '$cost'}}}])['result']
        if len(records_result) > 0:
            total_consume = records_result[0]['sum']
        counts = records.count()
        current_page = int(self.get_argument("p", 1))
        pages = int(round(counts / 10.0))
        if pages == 0:
            pages = 1
        if current_page <= 1:
            prev_page = 1
            next_page = 1
        else:
            prev_page = current_page - 1
            next_page = current_page + 1

        records = records.skip(per * (current_page - 1)).sort("_id", pymongo.DESCENDING).limit(10)

        def product_info(pid):
            return self.db.product.find_one({"id": pid})

        self.render("account/my_order.html", account_tab=20, records=records, counts=counts, product_info=product_info,
                    order_status=order_status, current_page=current_page, pages=pages, total_consume=total_consume,
                    prev_page=prev_page,
                    next_page=next_page, myuser=self.user)


class AccountInfoSetting(BaseHandler):
    """更新资料"""

    @BaseHandler.check_pwd_protect
    @BaseHandler.is_active
    @BaseHandler.is_check
    def get(self):
        error = ""
        self.render("account/info_setting.html", current_tab=1, error=error, myuser=self.user)
    @BaseHandler.is_active
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
    @BaseHandler.is_active
    @BaseHandler.is_check
    def get(self):
        error = ""
        self.render("account/pwd_update.html", current_tab=1, error=error, myuser=self.user)

    @BaseHandler.is_active
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
    @BaseHandler.is_active
    def get(self):
        error = ""
        self.render("account/pwd_protect.html", current_tab=1, error=error, myuser=self.user)
    @BaseHandler.is_active
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
    @BaseHandler.is_active
    @BaseHandler.authenticated
    def get(self):
        error = ""
        self.render("account/verify_safe_pwd.html", current_tab=1, next_url="", error=error, myuser=self.user)
    @BaseHandler.is_active
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
    @BaseHandler.is_active
    @BaseHandler.authenticated
    def get(self):
        reward_type = self.settings['reward_type']
        records = self.db.reward_record.find({"uid": self.user.get("uid")})
        self.render("account/award_record.html", current_tab=2, reward_type=reward_type, records=records,
                    myuser=self.user)


class AccountMembers(BaseHandler):
    """直属会员"""
    @BaseHandler.is_active
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
