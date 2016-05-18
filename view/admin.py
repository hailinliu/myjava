# encoding:utf-8
import json
import random
import time
from datetime import datetime
from datetime import date
from bson import DBRef, ObjectId
import datetime
import math
import tornado

from tornado.web import RequestHandler, StaticFileHandler

from BaseHandler import BaseHandler

from utils.mail import MailHandler
from pymongo import DESCENDING
import pymongo


class AdminLoginHandler(BaseHandler):
    """登录"""

    def get(self):
        # tornado.web.RequestHandler._template_loaders.clear()
        nexts = self.request.arguments.get("next")
        referer_url = '/admin/home'
        if 'Referer' in self.request.headers:
            referer_url = '/' + '/'.join(self.request.headers['Referer'].split("/")[3:])
        error = ""
        if self.user:
            if self.user.get("role", "") in ['admin', "superadmin"]:
                print self.user.get("role", "")
                self.redirect(referer_url)
                error = ""
            else:
                error = u"您已登录账号:%s,如继续则退出当前账号" % self.user['uid']

        next = referer_url
        if nexts:
            next = nexts[0]
        else:
            url = ""
        self.render("admin/login.html", url=next, myuser=self.user, error=error)

    def post(self, *args, **kwargs):

        print [value[0] for key, value in self.request.arguments.items() if key != '_xsrf']
        url, pwd, name = (value[0] for key, value in self.request.arguments.items() if key != '_xsrf')
        if not pwd:
            self.render("admin/login.html")
        self.logging.info(('admin user  %s login in' % (name)))

        res = self.begin_admin_session(name, pwd)
        if not res:
            self.render("admin/login.html", myuser=self.user, url=url, error="用户名或密码不正确")

        admin_user = self.db.user.find_one({"username": name, "role": "superadmin"})
        if not admin_user:
            self.render("admin/login.html", myuser=self.user, url=url, error="非法用户,请输入管理员账号")

        # # 登录记录
        # get_ip = self.request.remote_ip
        # self.db.logininfo.insert({"uid": self.user['uid'], "ip": get_ip, "time": time.strftime("%Y-%m-%d %H:%M:%S")})

        if url == '/admin/login':
            self.redirect('/admin/home')
        else:
            self.redirect(url)


class AdminLogoutHandler(BaseHandler):
    """注销"""

    def get(self):
        self.post()

    def post(self):
        self.end_session()
        self.redirect('/admin/login')


class AdminHomeHandler(BaseHandler):
    """后台主页"""

    @BaseHandler.admin_authed
    def get(self):
        user_count = self.db.user.find().count()
        user_handle = self.db.user_handle.find({"handle": "2"}).sort("time", DESCENDING).limit(8)
        today = datetime.date.today()
        today_register_count = self.db.user.find({"regtime": {"$gte": str(today)}}).count()

        total_sum = self.db.provide_money.aggregate({'$group': {'_id': "", 'sum': {'$sum': '$money'}}})
        if len(total_sum['result']) > 0:
            total_provide_money = total_sum['result'][0]['sum']
        else:
            total_provide_money = 0
        today_total_provide_money = 0
        provide_help_count = self.db.provide_help.find({"status": "waiting"}).count()
        today_provide_help_count = self.db.provide_help.find(
            {"status": "waiting", "time": {"$gte": str(today)}}).count()

        provide_help_money_result = self.db.provide_help.aggregate(
            [{"$match": {"status": "waiting"}}, {"$group": {'_id': "", 'sum': {'$sum': '$jine'}}}])['result']
        if len(provide_help_money_result) > 0:
            provide_help_money_count = provide_help_money_result[0]['sum']
        else:
            provide_help_money_count = 0
        today_provide_help_result = self.db.provide_help.aggregate(
            [{"$match": {"time": {"$gte": str(today)}}},
             {"$group": {'_id': 0, 'sum': {'$sum': '$jine'}}}])['result']
        if len(today_provide_help_result) > 0:
            today_provide_help_money_count = today_provide_help_result[0]['sum']
        else:
            today_provide_help_money_count = 0

        self.render("admin/home.html", myuser=self.user, admin_nav=1, user_count=user_count,
                    total_provide_money=total_provide_money, provide_help_count=provide_help_count,
                    today_total_provide_money=today_total_provide_money,
                    today_provide_help_count=today_provide_help_count,
                    provide_help_money_count=provide_help_money_count,
                    today_provide_help_money_count=today_provide_help_money_count,
                    today_register_count=today_register_count, user_handle=user_handle)


class AdminNewsEdit(BaseHandler):
    """公告发布、编辑"""

    @BaseHandler.admin_authed
    def get(self):
        news_id = int(self.get_argument("id", 0))
        news = self.db.news.find_one({"id": news_id})
        if not news:
            news = {}
        self.render("admin/news_edit.html", myuser=self.user, news=news, news_id=news_id, admin_nav=3)

    @BaseHandler.admin_authed
    def post(self):
        info = self.request.arguments
        for key, value in info.items():
            info[key] = value[0]
            print key, value[0]
        del info['_xsrf']
        info = dict(info)

        news_id = int(info['id'])
        del info['id']
        if news_id:
            self.db.news.update({"id": news_id}, {"$set": info})
        else:
            # id自增1
            last = self.db.news.find().sort("id", pymongo.DESCENDING).limit(1)
            if last.count() > 0:
                lastone = dict()
                for item in last:
                    lastone = item
                info['id'] = int(lastone['id']) + 1
            else:
                info['id'] = 1
            info['time'] = time.strftime('%Y-%m-%d', time.localtime(time.time()))
            self.db.news.insert(info)
            print info
        return self.redirect("/admin/news")


class AdminNewsList(BaseHandler):
    """公告列表"""

    @BaseHandler.admin_authed
    def get(self):
        news = self.db.news.find().sort("_id", pymongo.DESCENDING)
        self.render("admin/news.html", myuser=self.user, admin_nav=2, news=news)

    @BaseHandler.admin_authed
    def delete(self):
        try:
            for value in self.request.arguments.values():
                self.db.news.remove({"id": int(value[0])})
        except Exception, e:
            print e
            self.write(json.dumps({"status": 'error', "msg": u"删除失败，请重试！"}))
        else:
            count = len(self.request.arguments)
            print 'handle %d itmes' % count
            self.write(json.dumps({"status": 'ok', "msg": "delete %d items." % count}))


class AdminUserList(BaseHandler):
    """用户列表"""

    @BaseHandler.admin_authed
    def get(self):
        if not self.user:
            self.redirect('/admin/login')
        # query = {"role": {"$ne": 'superadmin'}, "blacklist": {"$ne": 1}}
        query = {"blacklist": {"$ne": 1}}
        search = ""
        role = self.get_argument("role", None)
        if role:
            query.update({"role": role})
        if self.get_argument("page", None) in ["", None]:
            current_page = 1
        else:
            current_page = int(self.get_argument("page"))

        uid = self.get_argument("uid", None)
        if uid:
            query.update({"admin": uid})

        users = self.db.user.find(query)
        per = 20.0
        pages = int(math.ceil(users.count() / per))
        users = users.skip(int(per) * (current_page - 1)).limit(int(per)).sort("_id", pymongo.DESCENDING)
        counts = users.count()
        # uid 存在，则查询该用户下面的会员
        def member_count(uid):
            return self.db.user.find({"admin": uid}).count()

        def trade_count(uid):
            return self.db.trade_log.find({"uid": uid}).count()

        self.render("admin/users.html", myuser=self.user, admin_nav=2, current_page=current_page, pages=pages,
                    counts=counts, member_count=member_count, trade_count=trade_count, users=users, search=search,
                    role=role)

    @BaseHandler.admin_authed
    def delete(self):
        try:
            for value in self.request.arguments.values():
                print value[0]
                self.db.user.remove({"uid": value[0]})
        except Exception, e:
            print e
            self.write(json.dumps({"status": 'error', "msg": u"删除失败，请重试！"}))
        else:
            count = len(self.request.arguments)
            print 'handle %d itmes' % count
            self.write(json.dumps({"status": 'ok', "msg": "delete %d items." % count}))

    @BaseHandler.admin_authed
    def put(self):
        try:
            for value in self.request.arguments.values():
                self.db.user.update({"uid": value[0]}, {"$set": {"blacklist": 1}})
        except Exception, e:
            print e
            self.write(json.dumps({"status": 'error', "msg": u"更新失败，请重试！"}))
        else:
            count = len(self.request.arguments)
            print 'handle %d itmes' % count
            self.write(json.dumps({"status": 'ok', "msg": "update %d items." % count}))

    @BaseHandler.admin_authed
    def post(self):

        query = {"role": {"$ne": 'superadmin'}, "blacklist": {"$ne": 1}}
        search = self.get_argument("search", "").encode("utf-8")
        if search:
            query.update({"$or": [{'username': search}, {"uid": search}, {'phone': search}]})
        role = self.get_argument("role", None)
        if role:
            query.update({"role": role})
        if self.get_argument("page", None) in ["", None]:
            current_page = 1
        else:
            current_page = int(self.get_argument("page"))

        uid = self.get_argument("uid", None)
        if uid:
            query.update({"admin": uid})
        users = self.db.user.find(query)
        per = 20.0
        pages = int(math.ceil(users.count() / per))
        users = users.skip(int(per) * (current_page - 1)).limit(int(per))
        counts = users.count()
        # uid 存在，则查询该用户下面的会员
        def member_count(uid):
            return self.db.user.find({"admin": uid}).count()

        def trade_count(uid):
            return self.db.trade_log.find({"uid": uid}).count()

        self.render("admin/users.html", myuser=self.user, admin_nav=2, current_page=current_page, pages=pages,
                    counts=counts, member_count=member_count, trade_count=trade_count, search=search, users=users,
                    role=role)


class AdminCheckPhone(BaseHandler):
    """检查电话号码"""

    @BaseHandler.admin_authed
    def get(self):
        phone = self.get_argument("phone", None)
        exist = self.db.user.find_one({"phone": phone})
        if not exist:
            self.write(json.dumps({"status": 'ok'}))

        else:
            self.write(json.dumps({"status": 'error'}))


class AddUser(BaseHandler):
    """添加用户"""

    @BaseHandler.admin_authed
    def get(self):
        if not self.user:
            self.redirect('/admin/login')

        users = self.db.user.find({"role": {"$ne": 'superadmin'}})
        type = self.get_argument("type", None)
        id=self.get_argument("id","")
        user={}
        if id:
            user=self.db.user.find_one({"uid":id})
            if not user:
                user={}
        self.render("admin/add_user.html", myuser=self.user, admin_nav=2, user=user,type=type)

    @BaseHandler.admin_authed
    def post(self):
        UserID = self.get_argument('UserID', None)
        level = int(self.get_argument('level', 0))
        jinbi = int(self.get_argument('jinbi', 0))
        money = int(self.get_argument('money', 0))
        phone = self.get_argument('phone', None)
        username = self.get_argument("username", None)
        pwd = self.get_argument("pwd", None)
        user = self.db.user.find_one({"$or": [{'uid': UserID}, {"phone": phone}, {'username': username}]})
        if user:
            # self.logging.info(u'该用户名或用户编号已经注册')
            self.render("ok.html", myuser=self.user, url="/admin/adduser", tip=u"该用户名或用户编号或手机号已经注册")
            # return self.write(json.dumps({"msg": u'该用户名或用户编号已经注册', "error": 'error'}))
        else:
            # baseurl = "http://cdn.zi-han.net/im/temp/"
            user = {
                'uid': UserID,
                'pwd': pwd,
                'phone': phone,
                'username': username,
                'level': level,
                'jinbi': jinbi,
                'money': money,
                'regtime': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())),
                'safe_pwd': pwd,
                'is_check': False,
                'is_active': True,
                'reward': 0,
            }
            # print 'user%s'%user
            self.logging.info(('register user %s %s' % (user['uid'], user['pwd'])))
            res = self.application.auth.register(user)
            if not res:
                print "register error"
                self.render("ok.html", myuser=self.user, url="/admin/adduser", tip=u"注册失败")
        self.redirect('/admin/userlist')


class AdminUserUpdateMoney(BaseHandler):
    """修改用户激活币"""

    @BaseHandler.admin_authed
    def post(self):
        uid = self.get_argument("uid")
        money = self.get_argument("money")
        try:
            money = int(money)
        except Exception:
            return self.write(json.dumps({"status": "error", "error": "请输入合法的金额"}))

        exist_user = self.db.user.find_one({"uid": uid})
        if exist_user:
            self.db.user.update({"uid": uid}, {"$set": {"money": money}})
            self.write(json.dumps({"status": "ok"}))
        else:
            return self.write(json.dumps({"status": "error", "error": "用户不存在"}))


class AdminUserUpdateLevel(BaseHandler):
    """修改用户级别"""

    @BaseHandler.admin_authed
    def post(self):
        uid = self.get_argument("uid")
        level = self.get_argument("level", 0)
        try:
            level = int(level)
        except Exception:
            return self.write(json.dumps({"status": "error", "error": "请输入合法的金额"}))

        exist_user = self.db.user.find_one({"uid": uid})
        if exist_user:
            self.db.user.update({"uid": uid}, {"$set": {"level": level}})
            self.write(json.dumps({"status": "ok"}))
        else:
            return self.write(json.dumps({"status": "error", "error": "用户不存在"}))


class AdminUserUpdateJinbi(BaseHandler):
    """修改用户金币"""

    @BaseHandler.admin_authed
    def post(self):
        uid = self.get_argument("uid")
        jinbi = self.get_argument("jinbi", 0)
        try:
            jinbi = int(jinbi)
        except Exception:
            return self.write(json.dumps({"status": "error", "error": "请输入合法的数字"}))

        exist_user = self.db.user.find_one({"uid": uid})
        if exist_user:
            self.db.user.update({"uid": uid}, {"$set": {"jinbi": jinbi}})
            self.write(json.dumps({"status": "ok"}))
        else:
            return self.write(json.dumps({"status": "error", "error": "用户不存在"}))


class AdminUserTradeRecord(BaseHandler):
    """用户交易记录
    :type 充值  转账
    """

    @BaseHandler.admin_authed
    def get(self):
        uid = self.get_argument("uid", "")
        user = self.db.user.find_one({"uid": uid})
        trade_records = self.db.trade_log.find({"uid": uid})
        self.render('admin/user_trade_record.html', admin_nav=3, user=user, trade_records=trade_records,
                    myuser=self.user)


class AdminUserApplyCrashRecord(BaseHandler):
    """用户申请提现记录
    :type 充值  转账
    """

    @BaseHandler.admin_authed
    def get(self):
        query = {}
        if self.get_argument("page", None) in ["", None]:
            current_page = 1
        else:
            current_page = int(self.get_argument("page"))

        search = ""
        records = self.db.apply_crash.find()
        per = 20.0
        pages = int(math.ceil(records.count() / per))
        records = records.skip(int(per) * (current_page - 1)).limit(int(per)).sort("_id", pymongo.DESCENDING)
        counts = records.count()

        def user_info(uid):
            info = self.db.user.find_one({"uid": uid})
            if not info:
                info = {}
            return info

        self.render('admin/crash_log.html', admin_nav=8, user_info=user_info, pages=pages, counts=counts,
                    records=records,
                    current_page=current_page, myuser=self.user, search=search)


class AdminUserResetPwd(BaseHandler):
    """修改密码"""

    @BaseHandler.admin_authed
    def get(self):
        uid = self.get_argument("uid", "")
        info = self.db.user.find_one({"uid": uid})
        self.render('admin/update_pwd.html', admin_nav=3, uid=uid, myuser=self.user, info=info)

    @BaseHandler.admin_authed
    def post(self):
        datas = self.request.arguments
        # print datas
        uid = self.get_argument("uid", '')
        pwd = self.get_argument("pwd")
        if not self.application.auth.changepwd(uid, pwd):
            self.render("ok.html", url="/admin/userlist", tip="密码修改失败")
        else:
            self.render("ok.html", url="/admin/userlist", tip="密码已修改")
        info = self.db.user.find_one({"uid": uid})
        self.render('admin/update_pwd.html', admin_nav=3, myuser=self.user, info=info)


class AdminUserResetPwdProtect(BaseHandler):
    """修改密码密保"""

    @BaseHandler.admin_authed
    def get(self):
        uid = self.get_argument("uid", "")
        # print uid
        info = self.db.user.find_one({"uid": uid})
        if not info:
            self.render("ok.html", url="/admin/userlist", tip="密码保护重置失败")
        else:
            self.db.user.update({"uid": uid}, {"$unset": {"question": 1, "answer": 1}})
            self.render("ok.html", url="/admin/userlist", tip="密码保护已重置")


class AdminUserFrozen(BaseHandler):
    """冻结用户"""

    @BaseHandler.admin_authed
    def get(self):
        uid = self.get_argument("uid", 0)
        type = self.get_argument("type", "")
        print uid
        info = self.db.user.find_one({"uid": uid})
        if not info:
            self.render("ok.html", url="/admin/userlist", tip="用户不存在")
        else:
            if type == 'cancel':
                self.db.user.update({"uid": uid}, {"$set": {"frozen": False}})
                self.render("ok.html", url="/admin/userlist", tip="用户已解冻")
            else:
                self.db.user.update({"uid": uid}, {"$set": {"frozen": True}})
                self.render("ok.html", url="/admin/userlist", tip="用户已被冻结")


class AdminContactRecord(BaseHandler):
    """反馈记录"""

    def get(self):
        record = self.db.contact.find()
        self.render("admin/contact_record.html", admin_nav=2,record=record, myuser=self.user)

    def post(self):
        record = self.db.contact.find()
        self.render("admin/contact_record.html", admin_nav=2,record=record,myuser=self.user)

class AdminPaidCrash(BaseHandler):
    """确认提现"""

    @BaseHandler.admin_authed
    def get(self):
        id = int(self.get_argument("id", 0))
        type = self.get_argument("type", "paid")
        print id
        info = self.db.apply_crash.find_one({"id": id})
        update_info = {}

        if not info:
            self.render("ok.html", url="/admin/crash_record", tip="该记录不存在")
        else:
            update_info = {"handle_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))}
            if type == 'paid':
                update_info.update({"status": "paid"})
                self.db.apply_crash.update({"id": id}, {"$set": update_info})
                self.render("ok.html", url="/admin/crash_record", tip="已处理")
            else:
                update_info.update({"status": "refuse"})
                self.db.apply_crash.update({"id": id}, {"$set": update_info})
                self.render("ok.html", url="/admin/crash_record", tip="已处理")


class AdminPetEdit(BaseHandler):
    """宠物发布、编辑"""

    @BaseHandler.admin_authed
    def get(self):
        pet_id = int(self.get_argument("id", 0))
        pet = self.db.pet.find_one({"id": pet_id})
        if not pet:
            pet = {}
        self.render("admin/pet_edit.html", myuser=self.user, pet=pet, pet_id=pet_id, admin_nav=3)

    @BaseHandler.admin_authed
    def post(self):
        try:
            pet_id = int(self.get_argument("id", 0))
            name = self.get_argument("name", "")
            level = int(self.get_argument("level", 0))
            price = int(self.get_argument("price", 0))
            day_jinbi = int(self.get_argument("day_jinbi", 0))
            limit = int(self.get_argument("limit", 0))
            life = int(self.get_argument("life", 0))
            image = self.get_argument("image", "")
            desc = self.get_argument("desc", "")

        except:
            return self.render("ok.html", myuser=self.user, url="/admin/pet_edit", tip=u"请输入合法的信息")
        info = {
            "id": pet_id,
            "name": name,
            "image": image,
            "level": level,
            "price": price,
            "day_jinbi": day_jinbi,
            "limit": limit,
            "life": life,
            "desc":desc
        }

        if pet_id:
            self.db.pet.update({"id": pet_id}, {"$set": info})
        else:
            # id自增1
            last = self.db.pet.find().sort("id", pymongo.DESCENDING).limit(1)
            if last.count() > 0:
                lastone = dict()
                for item in last:
                    lastone = item
                info['id'] = int(lastone['id']) + 1
            else:
                info['id'] = 1
            info['time'] = time.strftime('%Y-%m-%d', time.localtime(time.time()))
            self.db.pet.insert(info)
            # print info
        return self.redirect("/admin/petlist")


class AdminPetList(BaseHandler):
    """宠物列表"""

    @BaseHandler.admin_authed
    def get(self):
        pets = self.db.pet.find().sort("_id", pymongo.DESCENDING)
        self.render("admin/pets.html", myuser=self.user, admin_nav=3, pets=pets)

    @BaseHandler.admin_authed
    def delete(self):
        try:
            for value in self.request.arguments.values():
                self.db.pet.remove({"id": int(value[0])})
        except Exception, e:
            print e
            self.write(json.dumps({"status": 'error', "msg": u"删除失败，请重试！"}))
        else:
            count = len(self.request.arguments)
            print 'handle %d itmes' % count
            self.write(json.dumps({"status": 'ok', "msg": "delete %d items." % count}))


class AdminProductAdd(BaseHandler):
    """商品发布、编辑"""

    @BaseHandler.admin_authed
    def get(self):
        product_id = int(self.get_argument("id", 0))
        product = self.db.product.find_one({"id": product_id})
        if not product:
            product = {}
        self.render("admin/add_product.html", myuser=self.user, product=product, product_id=product_id, admin_nav=5)

    @BaseHandler.admin_authed
    def post(self):
        info = self.request.arguments
        for key, value in info.items():
            info[key] = value[0]
            print key, value[0]
        del info['_xsrf']
        info = dict(info)

        news_id = int(info['id'])

        del info['id']

        if news_id:
            self.db.product.update({"id": news_id}, {"$set": info})
        else:
            # id自增1
            last = self.db.product.find().sort("id", pymongo.DESCENDING).limit(1)
            if last.count() > 0:
                lastone = dict()
                for item in last:
                    lastone = item
                info['id'] = int(lastone['id']) + 1
            else:
                info['id'] = 1
            info['time'] = time.strftime('%Y-%m-%d', time.localtime(time.time()))
            self.db.product.insert(info)
            # print info
        return self.redirect("/admin/products")


class AdminProductList(BaseHandler):
    """商品列表"""

    @BaseHandler.admin_authed
    def get(self):
        products = self.db.product.find().sort("_id", pymongo.DESCENDING)
        self.render("admin/products.html", myuser=self.user, admin_nav=5, products=products)

    @BaseHandler.admin_authed
    def delete(self):
        try:
            for value in self.request.arguments.values():
                self.db.product.remove({"id": int(value[0])})
        except Exception, e:
            print e
            self.write(json.dumps({"status": 'error', "msg": u"删除失败，请重试！"}))
        else:
            count = len(self.request.arguments)
            print 'handle %d itmes' % count
            self.write(json.dumps({"status": 'ok', "msg": "delete %d items." % count}))


class AdminOrder(BaseHandler):
    """订单列表"""

    @BaseHandler.admin_authed
    def get(self):
        order_status = {"submit": "待发货", "shipped": "已发货"}
        orders = self.db.product_order.find().sort("_id", pymongo.DESCENDING)

        def address_info(uid):
            info=self.db.user.find_one({"uid": uid})
            if not info:
                return {}
            return info.get("address_info", {})
        def product_info(pid):
            return self.db.product.find_one({"id": pid})

        self.render("admin/orders.html", myuser=self.user, admin_nav=6, address_info=address_info,
                    product_info=product_info, order_status=order_status, orders=orders)

    @BaseHandler.admin_authed
    def delete(self):
        try:
            for value in self.request.arguments.values():
                self.db.product_order.remove({"id": int(value[0])})
        except Exception, e:
            print e
            self.write(json.dumps({"status": 'error', "msg": u"删除失败，请重试！"}))
        else:
            count = len(self.request.arguments)
            print 'handle %d itmes' % count
            self.write(json.dumps({"status": 'ok', "msg": "delete %d items." % count}))


class AddressOrderShip(BaseHandler):
    """订单设为发货"""

    @BaseHandler.admin_authed
    def get(self):
        try:
            order_id = int(self.get_argument("id", 0))
        except Exception, e:
            order_id = 0

        order = self.db.product_order.find_one({"id": order_id})
        if not order:
            order = {}
        self.render("admin/order_shipped.html", myuser=self.user, admin_nav=6, order_id=order_id, order=order)

    @BaseHandler.admin_authed
    def post(self):
        order_id = int(self.get_argument("order_id", 0))
        remark = self.get_argument("remark", '')
        self.db.product_order.update({"id": order_id}, {"$set": {"status": "shipped", "remark": remark}})
        self.redirect('/admin/orders')


class AdminRecharge(BaseHandler):
    """充值激活币"""

    @BaseHandler.admin_authed
    def get(self):
        if not self.user:
            self.redirect('/admin/login')
        uid = self.get_argument("uid", None)
        if uid:
            user_info = self.db.user.find_one({"uid": uid})
        else:
            user_info = None
        self.render("admin/recharge.html", myuser=self.user, uid=uid, user_info=user_info, admin_nav=2)

    @BaseHandler.admin_authed
    def post(self):
        money = int(self.get_argument("money", 0))
        pay_type = self.get_argument("pay_type", "jihuobi")
        print pay_type
        uid = self.get_argument("uid", None)
        user_info = self.db.user.find_one({"uid": uid})
        handle = {"money": user_info.get('money', 0) + money}
        if pay_type=='jihuobi':
            handle.update(
                    { "money": user_info.get('money', 0) + money})

            self.db.user.update({"uid": uid}, {"$set": handle})
             # trade_log_id自增1
            last_trade_log = self.db.trade_log.find().sort("id", pymongo.DESCENDING).limit(1)
            if last_trade_log.count() > 0:
                lastone = dict()
                for item in last_trade_log:
                    lastone = item
                trade_log_id = int(lastone.get('id', 0)) + 1
            else:
                trade_log_id = 1
            # 激活币转账记录
            self.db.trade_log.insert({
                "id": trade_log_id,
                "uid": self.user.get("uid"),
                "type": "transfer",
                "mid": uid, "money": money,
                "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))})
        else:
            # trade_log_id自增1
            last_trade_log = self.db.jinbi.find().sort("id", pymongo.DESCENDING).limit(1)
            if last_trade_log.count() > 0:
                lastone = dict()
                for item in last_trade_log:
                    lastone = item
                trade_log_id = int(lastone.get('id', 0)) + 1
            else:
                trade_log_id = 1

            now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))


            # 金币转入记录
            self.db.jinbi.insert({
                "id": trade_log_id + 1,
                "type": "in",
                "uid": uid,
                "mid": self.user.get("uid"),
                "money": money,
                "time": now_time})
            self.db.user.update({"uid": uid},{"$inc":{"jinbi":money}})
        return self.redirect('/admin/userlist')


class BuyPetRecord(BaseHandler):
    """购买宠物记录"""
    @BaseHandler.authenticated
    def get(self):
        if self.get_argument("page", None) in ["", None]:
            current_page = 1
        else:
            current_page = int(self.get_argument("page"))
        record=self.db.my_pet.find()
        per = 20.0
        pages = int(math.ceil(record.count() / per))
        record = record.skip(int(per) * (current_page - 1)).limit(int(per)).sort("_id", pymongo.DESCENDING)
        counts = record.count()
        def pet_info(id):
            pet=self.db.pet.find_one({"id":id})
            if not pet:
                return {}
            return  pet
        # 计算宠物当前存活天数
        def cal_life_day(buy_time):
            now_time=datetime.datetime.now()
            b = datetime.datetime.strptime(buy_time, '%Y/%m/%d %H:%M:%S')
            days= (now_time-b).days
            return days
        self.render("admin/buy_pet_record.html", myuser=self.user, record=record, cal_life_day=cal_life_day,pet_info=pet_info,pages=pages,counts=counts,current_page=current_page,
                    admin_nav=2)

class CheckoutJinBi(BaseHandler):
    """结算当天矿机金币"""
    @BaseHandler.authenticated
    def get(self):
        today = time.strftime("%Y-%m-%d")
        now_time = str(datetime.datetime.now())
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        my_pets = self.db.my_pet.find({"dead": {"$ne": 0}})
        for p in my_pets:
            info = {}
            uid = p.get("uid")
            pet_id = p.get("id")
            pid= p.get("pid")
            pet =self.db.pet.find_one({"id":pid})
            day_jinbi = pet.get("day_jinbi")
            gain = day_jinbi
            life = pet.get('life')
            now_time = datetime.datetime.now()
            buy_time = p.get("time")
            b = datetime.datetime.strptime(buy_time, '%Y/%m/%d %H:%M:%S')
            live_days = 1
            end_date=(b+datetime.timedelta(life)).date()
            print end_date
            print live_days*day_jinbi
            if p.get("check_day") != str(today):
                if end_date == now_time.date():
                    info.update({"dead": 1})
                producted_jinbi=live_days*day_jinbi
                info.update({"gain": gain, "check_day": today,"producted_jinbi":producted_jinbi})
                self.db.my_pet.update({"_id": ObjectId(p['_id'])}, {"$set": info})
                # 写入金币收入记录
                self.db.jinbi.insert({"type": 'pet_produce', 'money': gain, "pet_id": pet_id, "time": str(now_time)})
                self.db.user.update({"uid": uid}, {"$inc": {"jinbi": gain}})
        self.redirect("/admin/buy_pet_record")

class AdminLeaderRewardSetting(BaseHandler):
    """领导奖设置"""

    @BaseHandler.admin_authed
    def get(self):
        info = self.db.setting.find_one({"type": 1})
        if not info:
            info = {}
        self.render('admin/leader_award_setting.html', admin_nav=3, myuser=self.user, info=info)

    @BaseHandler.admin_authed
    def post(self):
        datas = self.request.arguments
        print datas

        if self.get_argument("recommend_jinbi") == "":
            recommend_jinbi =18
        else:
            recommend_jinbi = int(self.get_argument("recommend_jinbi", 18))
        self.db.setting.update({"type": 1}, {
            "$set": {"recommend_award": recommend_jinbi}},upsert=True)
        info=self.db.setting.find_one({"type": 1})
        self.render('admin/leader_award_setting.html', admin_nav=3, myuser=self.user, info=info)

class AdminPaiMaiRecord(BaseHandler):
    """拍卖纪录"""
    @BaseHandler.admin_authed
    def get(self):
        query={"type": "guadan"}


        search = ""

        if self.get_argument("page", None) in ["", None]:
            current_page = 1
        else:
            current_page = int(self.get_argument("page"))

        record = self.db.jinbi.find(query)
        per = 20.0
        pages = int(math.ceil(record.count() / per))
        record = record.skip(int(per) * (current_page - 1)).limit(int(per)).sort("_id", pymongo.DESCENDING)
        counts = record.count()
        self.render('admin/paimai_record.html', admin_nav=9, myuser=self.user, search="",current_page=current_page,pages=pages,counts=counts,
                    record=record)