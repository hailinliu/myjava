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
from utils import random_code, send_short_msg


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
        cap_ch = self.get_argument("cap_ch", None)
        cookiecode = self.get_secure_cookie('verify_code')
        if cap_ch:
            if cap_ch != cookiecode:
                return self.render("account/login.html", url="", error=u"验证码不正确")
            else:
                self.set_secure_cookie("checked", "checked")
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
                return self.render("account/login.html", url=url, error=u"该账号已被冻结")
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
        username = self.get_argument('username', None)
        phone = self.get_argument('phone', None)
        pwd = self.get_argument('password', None)
        safe_pwd = self.get_argument('safe_pwd', None)
        real_name = self.get_argument('safe_pwd', "")
        id_code = self.get_argument('id_code', "")
        qq = self.get_argument('qq', "")
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
                exist_reco_user = self.db.user.find_one({"uid": rName})
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
                'username': username,
                'regtime': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())),
                'safe_pwd': safe_pwd,
                'admin': rName,
                'real_name':real_name,
                'id_code':id_code,
                'qq':qq,
                'money': 0,
                'level': 0,
                'jinbi': 0,
                'is_active': False,
            }
            logging.info(('register user %s %s' % (user['uid'], user['pwd'])))
            res = self.application.auth.register(user)
            if not res:
                return self.render("error.html", myuser=self.user, r=rName, error=u"注册失败")
            else:
                now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))

                return self.render("ok.html", myuser=self.user, r=rName, url="/user/home", tip=u"注册成功")


class Draw(BaseHandler):
    """抽奖"""

    @BaseHandler.authenticated
    def get(self):
        self.render('site/choujiang.html', myuser=self.user)


class GetPrize(BaseHandler):
    """获取奖品数据"""

    def check_xsrf_cookie(self):
        pass

    @BaseHandler.authenticated
    def get(self):
        prize = [{"id": 1, "prize": "商城价值500的商品", "v": 1.0}, {"id": 2, "prize": "100金币", "v": 1.5},
                 {"id": 3, "prize": "10金币", "v": 2.0}]
        left_jinbi = self.db.user.find_one({"uid": self.user.get("uid")}).get("jinbi", 0)
        date = str(datetime.datetime.today().date())
        draw_count = self.db.draw.find({"uid": self.user.get("uid"), "date": date}).count()
        if draw_count >= 3:
            return self.write(json.dumps({"status": "error", "error": "今天抽奖机会已用完"}))
        return self.write(json.dumps({"status": "ok", "prize": prize, "jinbi": left_jinbi}))

    @BaseHandler.authenticated
    def put(self):
        prize = int(self.get_argument("prize", 0))
        handle_id = int(self.get_argument("handle_id", 0))
        left_jinbi = self.user.get("jinbi")

        if prize in [1, 2]:
            if prize == 1:
                prize_jinbi = 100
            else:
                prize_jinbi = 10
            self.db.user.update({"uid": self.user.get("uid")}, {"$set": {"jinbi": left_jinbi + prize_jinbi}})
            self.db.draw.update({"id": handle_id}, {"$set": {"prize": prize}})
        left_jinbi = self.db.user.find_one({"uid": self.user.get("uid")}).get("jinbi", 0)
        print left_jinbi
        return self.write(json.dumps({"status": "ok", "jinbi": left_jinbi}))

    @BaseHandler.authenticated
    def post(self):
        prize = [{"id": 1, "prize": "商城价值500的商品", "v": 1.0}, {"id": 2, "prize": "100金币", "v": 1.5},
                 {"id": 3, "prize": "10金币", "v": 2.0}]
        left_jinbi = self.db.user.find_one({"uid": self.user.get("uid")}).get("jinbi", 0)
        date = str(datetime.datetime.today().date())
        draw_count = self.db.draw.find({"uid": self.user.get("uid"), "date": date}).count()
        now_time = time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(time.time()))
        # id自增1
        last = self.db.draw.find().sort("id", pymongo.DESCENDING).limit(1)
        if last.count() > 0:
            lastone = dict()
            for item in last:
                lastone = item
            draw_id = int(lastone.get('id', 0)) + 1
        else:
            draw_id = 1

        if left_jinbi > 2:
            if draw_count < 3:
                date = str(datetime.datetime.today().date())
                self.db.user.update({"uid": self.user.get("uid")}, {"$set": {"jinbi": left_jinbi - 2}})
                self.db.draw.insert({"id": draw_id, "uid": self.user.get("uid"), "date": date})
                last_trade_log = self.db.jinbi.find().sort("id", pymongo.DESCENDING).limit(1)
                if last_trade_log.count() > 0:
                    lastone = dict()
                    for item in last_trade_log:
                        lastone = item
                    jinbi_id = int(lastone.get('id', 0)) + 1
                else:
                    jinbi_id = 1
                self.db.jinbi.insert(
                    {"id": jinbi_id, "type": "draw", "uid": self.user.get("uid"), "money": 2, "time": now_time})
            else:
                return self.write(json.dumps({"status": "error", "error": "今天抽奖机会已用完"}))
        return self.write(json.dumps({"status": "ok", "prize": prize, "jinbi": left_jinbi}))


class ContactUs(BaseHandler):
    """站内留言"""

    def get(self):
        record = self.db.contact.find({"uid": self.user.get("uid")})
        self.render("site/contactus.html", record=record, account_tab=1, myuser=self.user)

    def post(self):
        record = self.db.contact.find({"uid": self.user.get("uid")})
        question = self.get_argument("question", "")
        title = self.get_argument("title", "")
        content = self.get_argument("content", "")
        # id自增1
        last = self.db.contact.find().sort("id", pymongo.DESCENDING).limit(1)
        if last.count() > 0:
            lastone = dict()
            for item in last:
                lastone = item
            id = int(lastone.get('id', 0)) + 1
        else:
            id = 1
        now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.db.contact.insert(
            {"uid": self.user.get("uid"), "question": question, "title": title, "content": content, "id": id,
             "time": now_time})
        return self.redirect('/user')


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
        self.render("site/notice_detail.html", news=news, account_tab=1, myuser=self.user)


class NoticeList(BaseHandler):
    """公告列表"""

    def get(self):
        news = self.db.news.find()
        self.render("site/notice_list.html", news=news, account_tab=1, myuser=self.user)


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
        print items
        now_time = time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(time.time()))
        for i in items:
            pet = self.db.pet.find_one({"id": i['id']})
            # TODO 校验
            count = int(i['count'])
            if count > pet['limit']:
                return self.render("ok.html", myuser=self.user, url="/nongchangsd",
                                   tip=u"%s限购%d个" % (pet['name'], pet['limit']))
            else:
                # 查找已购买的未过期的红包数是否超过限制
                bought_count = self.db.my_pet.find(
                    {"pid": pet['id'], "uid": self.user.get("uid"), "dead": {"$ne": 1}}).count()
                if bought_count + count > pet['limit']:
                    return self.render("ok.html", myuser=self.user, url="/nongchangsd",
                                       tip=u"%s分红进行中%d个,限购%d个" % (pet['name'], bought_count, pet['limit']))

            price = pet['price']
            item_cost = int(price) * int(count)
            total_cost += item_cost
            if total_cost <= self.user.get("jinbi"):
                self.db.user.update({"uid": self.user.get("uid")}, {"$inc": {"jinbi": -total_cost}})
            else:
                return self.render("ok.html", myuser=self.user, url="/nongchangsd", tip=u"金币余额不足")
            # id自增1
            last = self.db.my_pet.find().sort("id", pymongo.DESCENDING).limit(1)
            if last.count() > 0:
                lastone = dict()
                for item in last:
                    lastone = item
                oid = int(lastone.get('id', 0)) + 1
            else:
                oid = 1
            for a in range(0, count):
                self.db.my_pet.insert({"id": oid, "pid": i['id'], "count": count, "uid": self.user.get('uid'),
                                       "time": now_time})
                oid += 1
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

        # TODO 计算投资推荐分红-管理奖
        award_percent = [10, 7, 5, 3, 1]
        user = self.user
        for per in award_percent:
            # 查询一代
            admin_id = user.get("admin")
            admin_user = self.db.user.find_one({"uid": admin_id})
            if admin_user:
                # id自增1
                last = self.db.jinbi.find().sort("id", pymongo.DESCENDING).limit(1)
                if last.count() > 0:
                    lastone = dict()
                    for item in last:
                        lastone = item
                    consume_id = int(lastone.get('id', 0)) + 1
                print admin_id, total_cost * per / 100
                reward = total_cost * per / 100
                self.db.jinbi.insert(
                    {"uid": admin_id, "type": "admin_award", "id": consume_id, "time": now_time,
                     "money": reward})
                self.db.user.update({"uid": admin_id}, {"$inc": {"jinbi": reward}})
                user = admin_user

        return self.render("ok.html", myuser=self.user, url="/nongchangsd", tip=u"购买成功")


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


# 注册验证码
class ForgetPwdSendCode(BaseHandler):
    """发送验证码"""

    def get(self):
        mobile_number = self.get_argument("mobile_number")
        msg_code = random.randint(100000, 999999)
        self.set_cookie('msg_code', str(msg_code))
        print self.get_cookie('msg_code')

        last_request_time = datetime.datetime.now() - datetime.timedelta(minutes=1)
        # 查找一分钟内的register 验证码请求记录
        record = self.db.request_record.find_one(
            {"type": "forget_pwd", "ip": self.request.remote_ip, "time": {"$gte": last_request_time}})
        permit = False if record else True
        if permit:
            tpl_value = "#code#=%s" % (str(msg_code))
            print tpl_value
            send_short_msg('1343305', tpl_value, mobile_number)
            # 写入请求记录表
            self.db.request_record.insert(
                {"time": datetime.datetime.now(), "type": "register", "ip": self.request.remote_ip})
            self.write(json.dumps({"msg": 'ok', "error": ''}))
        else:
            self.write(json.dumps({"msg": '请勿频繁请求', "error": 'error'}))


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
