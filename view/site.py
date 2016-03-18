# encoding: utf-8
import json
import logging
import os
import random
import re
from urllib import urlencode
import uuid
import time
import datetime
from passlib.handlers.pbkdf2 import pbkdf2_sha512
from pymongo import DESCENDING
import pymongo
from BaseHandler import BaseHandler
from utils import random_code


class MainHandler(BaseHandler):
    def get(self):
        self.render("site/index.html", current_tab=1, myuser=self.user)


class RightHandler(BaseHandler):
    @BaseHandler.authenticated
    def get(self):
        self.render("site/right.html", current_tab=1, myuser=self.user)


class LoginHandler(BaseHandler):
    """登录"""

    def get(self):
        # self._template_loaders.clear()
        next_url = self.get_argument("next", None)
        referer_url = '/user/home'
        if 'Referer' in self.request.headers:
            referer_url = '/' + '/'.join(self.request.headers['Referer'].split("/")[3:])
            print referer_url

        if not next_url:
            next_url = referer_url
        if referer_url == '/':
            next_url = '/user/home'
        self.render("account/login.html", url=next_url, error="")

    def post(self):
        self.logging.info(('LoginHandler argument %s') % (self.request.arguments))

        try:
            url = self.get_argument("url", None)
            pwd = self.get_argument("password", None)
            phone = self.get_argument("name", None)
        except Exception, e:
            print e
            self.render("account/login.html", url="", error=u"登录异常")

        else:
            if not pwd:
                self.render("account/login.html", url="", error=u"密码为空")

            exist_user = self.db.user.find_one({'phone': phone})
            if not exist_user:
                return self.render("account/login.html", url=url, myuser={},
                                   error=u"用户不存在(提示:手机号或用户名都可以登录)")

            # 查询用户是否被冻结
            if exist_user.get("frozen"):
                self.render("account/login.html", url=url, error=u"该用户已被冻结")
            res = self.begin_session(phone, pwd)
            if not res:
                return self.render("account/login.html", url=url, error=u"用户名或密码不正确")
            if self.user:
                # 登录记录
                get_ip = self.request.remote_ip
                if get_ip == '127.0.0.1':
                    get_ip = self.request.headers.get('X-Real-Ip', '未知')
                log_time = time.strftime("%Y-%m-%d %H:%M:%S")
                self.db.logininfo.insert(
                    {"uid": self.user.get("uid"), "ip": get_ip, "time": log_time})
                self.db.user.update({"uid": self.user['uid']}, {"$set": {"login": {"time": log_time, "ip": get_ip}}})
            print url
            if 'register' in url:
                return self.redirect('/login')
            elif 'login' in url:
                return self.redirect('/user/home')
            else:
                return self.redirect(url)


class Register(BaseHandler):
    """注册"""

    def get(self):
        r = self.get_argument("r", "")
        if not r:
            if self.user:
                r = self.user.get("phone")
            else:
                r = ""

        self.render("site/register.html", r=r, myuser=self.user)

    def post(self):
        print self.request.arguments
        rName = self.get_argument('rName', None)
        phone = self.get_argument('phone', None)
        pwd = self.get_argument('password', None)
        safe_pwd = self.get_argument('safe_pwd', None)
        exist_user = self.db.user.find({'uid': phone})
        inviter = None
        if None in [pwd, phone, safe_pwd]:
           return self.render("error.html", myuser=self.user, r=rName, error=u"请完善注册信息")
        exist_phone = self.db.user.find_one({"phone": phone})
        if exist_phone:
            return self.render("error.html", myuser=self.user, r=rName, error=u"该手机号码已注册")
        if exist_user.count() > 0:
            logging.info(u'该用户编号已存在')
            return self.render("error.html", myuser=self.user, r=rName, error=u"该用户编号或用户名已存在")
        else:
            if not rName:
                return self.render("error.html", myuser=self.user, r=rName, error=u"请输入介绍人编号")
            else:
                exist_reco_user = self.db.user.find_one({"phone": rName})
                if exist_reco_user:
                    inviter = exist_reco_user
                else:
                    return self.render("error.html", myuser=self.user, r=rName, error=u"该直推人会员编号不存在")
            if pwd == "":
                self.render("error.html", myuser=self.user, r=rName, error=u"密码不能为空")
            if phone == "":
                self.render("error.html", myuser=self.user, r=rName, error=u"手机号码不能为空")
            user = {
                'uid': phone,
                'phone': phone,
                'pwd': pwd,
                'username': phone,
                'regtime': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())),
                'safe_pwd': safe_pwd,
                'admin': rName,
                'money': 0,
                'level': 0,
                'jinbi':0,
                'is_active': False,
            }
            logging.info(('register user %s %s' % (user['uid'], user['pwd'])))
            res = self.application.auth.register(user)
            if not res:
                print "register error"


                # 如果与介绍人编号一致的用户存在
                if inviter:
                    info = {
                        "no": "1",
                        "uid": rName,
                        "type": 1,
                        "money": inviter.get("money", 0) * 0.1,
                        "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())),
                    }

                    # self.db.reward_record.insert(info)
                    # # TODO 更新上级代理的奖金  10%
                    # self.db.user.update({"uid": rName}, {
                    #     "$set": {"reward": inviter.get("reward", 0) + inviter.get("money", 0) * 0.1}})

                return self.render("error.html", myuser=self.user, r=rName, error=u"注册失败")
            else:
                return self.render("ok.html", myuser=self.user, r=rName, url="/user/home", tip=u"注册成功")


class Draw(BaseHandler):
    """抽奖"""

    @BaseHandler.authenticated
    def get(self):
        self.render('site/choujiang.html')
class ForgetPwd(BaseHandler):
    """忘记密码"""

    def get(self):
        self.render('account/forget_pwd.html')

    def post(self):
        pass


class CheckNick(BaseHandler):
    def get(self):
        nickname = self.get_argument("nickname", None)

        if not nickname:
            self.render('error.html', error="您输入的会员编号不存在,请确认后再进行验证.")
        else:
            exist = self.db.user.find_one({"uid": nickname})
            if exist:
                tip = "推荐人编号:{0} \n姓名:{1} \n验证通过".format(exist.get("uid"), exist.get("username"))
                self.render('error.html', error=tip)
            else:
                self.render('error.html', error="您输入的会员编号不存在,请确认后再进行验证.")
        return self.write(json.dumps({"msg": 'ok', "error": ''}))


class NoticeDetail(BaseHandler):
    """公告详情"""

    def get(self):
        id = int(self.get_argument("id", 0))
        if id:
            news = self.db.news.find_one({"id": id})
        else:
            news = {}
        self.render("site/notice_detail.html", news=news, myuser=self.user)


class NoticeList(BaseHandler):
    """公告列表"""

    def get(self):
        news = self.db.news.find()
        cookie_safe_pwd = self.get_secure_cookie("safe_pwd")
        print cookie_safe_pwd
        if not cookie_safe_pwd or cookie_safe_pwd != self.user.get("safe_pwd"):
            if self.request.method in ("GET", "HEAD"):
                url = '/account/safe_pwd_check' + "?" + urlencode(dict(next=self.request.uri))
                return self.redirect(url)
        self.render("site/notice_list.html", news=news, myuser=self.user)


class FarmShop(BaseHandler):
    """农场商店"""

    @BaseHandler.authenticated
    def get(self):
        pets = self.db.pet.find()
        self.render("farm/nongchangsd.html", myuser=self.user, pets=pets, account_tab=3)

    @BaseHandler.authenticated
    def post(self):
        total_cost = 0
        items = self.get_argument("items")
        items = eval(items)
        order_items = []
        # print items
        now_time = time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(time.time()))
        for i in items:
            pet = self.db.pet.find_one({"id": i['id']})
            count = i['count']
            price = pet['price']
            item_cost = int(price) * int(count)
            total_cost += item_cost
            self.db.my_pet.insert({"pid": i['id'], "count": count, "uid": self.user.get('uid'),
                                   "time": now_time})
            order_items.append({
                "pid": i['id'],
                "count": count,
                "cost": item_cost})

        self.db.order.insert(
            {"item": order_items, "uid": self.user.get('uid'), "cost": total_cost, "time": now_time})

        # id自增1
        last = self.db.jinbi.find().sort("id", pymongo.DESCENDING).limit(1)
        if last.count() > 0:
            lastone = dict()
            for item in last:
                lastone = item
            consume_id = int(lastone.get('id', 0)) + 1
        else:
            consume_id = 1

        self.db.jinbi.insert(
            {"uid": self.user.get("uid"), "type": "buy_pet", "id": consume_id, "time": now_time, "money": total_cost})
        if total_cost <= self.user.get("jinbi"):
            self.db.user.update({"uid": self.user.get("uid")}, {"$inc": {"jinbi": -total_cost}})
        print total_cost
        return self.redirect('/nongchangsd')




class error_403(BaseHandler):
    def get(self):
        self.render("site/403.html")


class error_404(BaseHandler):
    def get(self):
        self.render("404.html")


class error_500(BaseHandler):
    def get(self):
        self.render("500.html")


class ProductList(BaseHandler):
    @BaseHandler.authenticated
    def get(self):
        member_count = self.db.user.find({"admin": self.user.get('uid')}).count()
        products = self.db.product.find().sort("_id", pymongo.DESCENDING)

        self.render("product/list.html", account_tab=19, products=products, member_count=member_count, myuser=self.user)

    @BaseHandler.authenticated
    def post(self):
        if not self.user.get("address_info"):
            return self.render("ok.html", myuser=self.user, url="/account/address_setting", tip=u"请先完善收货地址")
        total_cost = 0
        items = self.get_argument("items")
        items = eval(items)
        order_items = []
        # print items
        now_time = time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(time.time()))
        for i in items:
            product = self.db.product.find_one({"id": i['id']})
            count = i['count']
            price = product['price']
            item_cost = int(price) * int(count)
            total_cost += item_cost

            order_items.append({
                "pid": i['id'],
                "count": count,
                "cost": item_cost})
        if total_cost > int(self.user.get("jinbi")):
            return self.render("ok.html", myuser=self.user, url="/shop", tip=u"金币余额不足")

        # id自增1
        last = self.db.product_order.find().sort("id", pymongo.DESCENDING).limit(1)
        if last.count() > 0:
            lastone = dict()
            for item in last:
                lastone = item
            order_id = int(lastone.get('id', 0)) + 1
        else:
            order_id = 1
        self.db.product_order.insert(
            {"id": order_id, "item": order_items, "uid": self.user.get('uid'), "cost": total_cost, "status": "submit",
             "time": now_time})

        # id自增1
        last = self.db.consume.find().sort("id", pymongo.DESCENDING).limit(1)
        if last.count() > 0:
            lastone = dict()
            for item in last:
                lastone = item
            consume_id = int(lastone.get('id', 0)) + 1
        else:
            consume_id = 1

        self.db.consume.insert(
            {"uid": self.user.get("uid"), "type": "buy_pet", "id": consume_id, "time": now_time, "cost": total_cost})

        if total_cost <= self.user.get("jinbi"):
            self.db.user.update({"uid": self.user.get("uid")}, {"$inc": {"jinbi": -total_cost}})
        print total_cost
        return self.redirect('/shop')


class UploadImageFile(BaseHandler):
    # def check_xsrf_cookie(self):
    #     pass

    def post(self):
        path = self.get_argument("path")

        order_id = self.get_argument("order_id", None)
        upload_path = os.path.join(self.settings['upload_path'], path)
        # 若不存在此目录，则创建之
        if not os.path.isdir(upload_path):
            # upload_path = upload_path.replace("/", "\\")
            # os.makedirs(upload_path)
            os.mkdir(upload_path)
        file_metas = self.request.files.get('file', [])
        filename = ''
        try:
            for meta in file_metas:
                filename = meta['filename']
                ext = os.path.splitext(filename)[1]
                # 生成随机文件名
                filename = str(uuid.uuid4())
                filename = '%s%s' % (filename, ext)
                filepath = os.path.join(upload_path, filename)
                with open(filepath, 'wb') as up:
                    up.write(meta['body'])
        except Exception, e:
            self.write(json.dumps({"status": 'error', "msg": u"上传失败，请重新上传"}))
        else:
            # TODO 如果传入打款截图，则写入匹配记录
            if order_id:
                self.db.match_help.update({"order_id": order_id}, {"$set": {"pay_image": filename}})

            self.write(json.dumps({"status": 'ok', "msg": "", "base_url": "", "name": filename}))




class UploadImage(BaseHandler):
    def post(self):
        path = self.get_argument("path")
        upload_path = os.path.join(self.settings['upload_path'], path)
        # 若不存在此目录，则创建之
        if not os.path.isdir(upload_path):
            os.makedirs(upload_path.replace('/', '\\'))
        file_metas = self.request.files.get('file', [])
        filename = ''
        try:
            for meta in file_metas:
                filename = meta['filename']
                ext = os.path.splitext(filename)[1]
                # 生成随机文件名
                filename = str(uuid.uuid4())

                filename = '%s%s' % (filename, ext)
                filepath = os.path.join(upload_path, filename)
                with open(filepath, 'wb') as up:
                    up.write(meta['body'])
        except Exception, e:
            self.write(json.dumps({"error": 1, "msg": u"上传失败，请重新上传"}))
        else:
            self.write(json.dumps({"error": 0, "url": filename}))


class KindeditorUploadImage(BaseHandler):
    def post(self):
        now_date = time.strftime("%Y%m%d", time.localtime())
        upload_path = os.path.join(self.settings['upload_path'], "editor_upload/%s") % now_date
        base_url = "/static/media/editor_upload/%s/" % now_date
        # 若不存在此目录，则创建之
        if not os.path.isdir(upload_path):
            # os.makedirs(upload_path.replace('/', '\\'))
            os.makedirs(upload_path)
        file_metas = self.request.files.get('imgFile', [])
        filename = ''
        try:
            for meta in file_metas:
                filename = meta['filename']
                ext = os.path.splitext(filename)[1]
                # 生成随机文件名
                filename = str(uuid.uuid4())
                filename = '%s%s' % (filename, ext)
                filepath = os.path.join(upload_path, filename)
                filesize = len(meta['body'])
                with open(filepath, 'wb') as up:
                    up.write(meta['body'])
        except Exception, e:
            self.write(json.dumps({"error": 1, "msg": u"上传失败，请重新上传"}))
        else:
            # 上传记录
            self.db.upload_record.insert(
                {"uid": self.user['uid'], "filename": filename, "size": filesize, "dir_path": base_url,
                 "time": datetime.datetime.now()})
            self.write(json.dumps({"error": 0, "url": base_url + filename}))


class FileManagerJson(BaseHandler):
    def get(self):
        file_list = []
        for f in self.db.upload_record.find({"uid": self.user['uid']}):
            file_list.append({
                "is_dir": False,
                "has_file": False,
                "filesize": str(f.get('size', "")),
                "dir_path": f.get('dir_path', ""),
                "is_photo": True,
                "filetype": f['filename'][-3:],
                "filename": f['filename'],
                "datetime": str(datetime)
            })
        self.write(json.dumps(
            {"error": 0, "current_dir_path": "", "current_url": "", "total_count": len(file_list),
             "file_list": file_list}))
