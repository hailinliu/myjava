# -*- coding: utf-8 -*-
import tornado.ioloop
from tornado.httpserver import HTTPServer
from tornado.web import HTTPError
from tornado.options import define, options

from session.auth import MongoAuthentication
from session.session import MongoSessions
from utils.Notice import Notice
from utils.UImodule import *
from view.account import SafePwdCheck, AccountPwdUpdate, AccountPwdProtect, AccountInfoSetting, \
    AccountMembers, AccountAwardDetail, LogoutHandler, TuijianJg, Zhitui, Jihuo, JihuoRecord, JiHuobiLog, JiHuobiLog2, \
    JinBiLog, JinBiLog2, MyOrder, UserAddressSetting, UserAlipaySetting
from view.admin import *
from view.site import *
from view.trade import *
from view.user import *
from utils import VerifyCode
from utils.session import *

define("port", default=8000, help="run on the given port", type=int)
define("develop", default=True, help="develop environment", type=bool)
'''
    author:
        Robbin
    时间:
        2015/8/1
    服务端的架构体系:
        db  : weikefarm (mongodb)
        session : redis
        verify_code : 校验码验证--pillow
        msg_code  : 短信验证码--云片网api  http://www.yunpian.com
'''


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/403", error_403),
            (r"/404", error_404),
            (r"/500", error_500),
            (r"/register", Register),
            (r"/user/home", UserHomeHandler),
            (r"/checknickname", CheckNick),
            (r"/login", LoginHandler),
            (r"/logout", LogoutHandler),
            (r"/forget_pwd", LogoutHandler),
            (r"/news", NoticeDetail),
            (r"/news_list", NoticeList),
            (r"/mynongchang", MyFarm),
            (r"/nongchangsd", FarmShop),
            (r"/shop", ProductList),
            (r"/draw", Draw),
            (r"/account/tjjg", TuijianJg),
            (r"/account/zhitui", Zhitui),
            (r"/account/jihuo", Jihuo),
            (r"/account/jihuojl", JihuoRecord),
            (r"/account/jihuobi_log", JiHuobiLog),
            (r"/account/jihuobi_log2", JiHuobiLog2),
            (r"/account/jinbi_log", JinBiLog),
            (r"/account/jinbi_log2", JinBiLog2),
            (r"/account/orders", MyOrder),
            (r"/account/address_setting", UserAddressSetting),
            (r"/account/alipay_setting", UserAlipaySetting),
            (r"/account/info_setting", AccountInfoSetting),
            (r"/account/pwd_update", AccountPwdUpdate),
            (r"/account/pwd_protect", AccountPwdProtect),
            (r"/account/safe_pwd_check", SafePwdCheck),
            (r"/account/members", AccountMembers),
            (r"/account/reward_detail", AccountAwardDetail),
            (r"/trade/zhuanjihuobi", Zhuanjihuobi),
            (r"/trade/zhuanjinbi", Zhuanjinbi),
            (r"/trade/maijb", GetCrash),
            (r"/trade/jbdingdan", GetCrashLog),
            (r"/trade/jinbi_guadan", JinBiPaiMai),
            (r"/trade/woyao_guadan", JinBiGuadan),
            (r"/trade/jinbi_mai", JinBiGoumai),
            (r"/trade/jinbi_mai2", JinBiMai),
            (r"/trade/jinbi_qianggou", JinBiQianggou),
            (r"/trade/jinbi_confirm_pay", JinBiQuerenPay),
            (r"/trade/jinbi_cancel_pay", JinbiQianggouCancel),
            (r"/trade/jinbi_confirm_paid", JinBiConfirmPaid),
            (r"/admin/login", AdminLoginHandler),
            (r"/admin/loginout", AdminLogoutHandler),
            (r"/admin/home", AdminHomeHandler),
            (r"/admin/news", AdminNewsList),
            (r"/admin/news_edit", AdminNewsEdit),
            (r"/admin/userlist", AdminUserList),
            (r"/admin/reset_pwd", AdminUserResetPwd),
            (r"/admin/reset_pwd_protect", AdminUserResetPwdProtect),
            (r"/admin/frozen_user", AdminUserFrozen),
            (r"/admin/check_phone", AdminCheckPhone),
            (r"/admin/update_money", AdminUserUpdateMoney),
            (r"/admin/update_level", AdminUserUpdateLevel),
            (r"/admin/update_jinbi", AdminUserUpdateJinbi),
            (r"/admin/adduser", AddUser),
            (r"/admin/petlist", AdminPetList),
            (r"/admin/addpet", AdminPetEdit),
            (r"/admin/add_product", AdminProductAdd),
            (r"/admin/products", AdminProductList),
            (r"/admin/orders", AdminOrder),
            (r"/admin/order_shippd", AddressOrderShip),
            (r"/verifycode", VerifyCode),
            (r"/sendcode", RegisterSendCode),
            (r"/ajax/upload_image", UploadImageFile),
            (r"/kindeditor_upload_json", KindeditorUploadImage),
            (r"/file_manager_json", FileManagerJson),

        ]
        ui_modules = {
            'LoginState': LoginStateModule,  # 是否登录
            'random': RandomStrModule,  # 生成随机数
            'header': HeaderModule,  # 头部
            'GetUserNameById': GetUserNameById,  # uid-->username
            'noticeTpl': NoticeModule,  # 系统通知
            'Unread': Unread,  # 未读消息
            'messageTpl': MessageModule,

        }
        self.sessions = MongoSessions("weikefarm", "sessions", timeout=30)

        self.auth = MongoAuthentication("weikefarm", "user")
        self.sessions.clear_all_sessions()
        settings = dict(
            cookie_secret="e446976943b4e8442f099fed1f3fea28462d5832f483a0ed9a3d5d3859f==78d",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            upload_path=os.path.join(os.path.dirname(__file__), "static/media"),
            json_path=os.path.join(os.path.dirname(__file__), "json"),
            xsrf_cookies=True,
            login_url='/login',
            admin_login_url="/admin/login",
            attachment_upload_url="http://112.74.133.196:8005/upload_attachment",
            attachment_path=os.path.join(os.path.dirname(__file__), "attachment"),
            plan_type={"funding": 1, "hiring": 2, "place": 3},  # 计划类型
            user_handle={"add": "0", "del": "1", "online": "2"},  # 用户操作类型:发布、删除、审核通过（上线）
            type={"project": "0", "activity": "1", "park": "2", "course": "3", "job": "4"},  # 项目、活动、创业园、
            status={"editing": "未提交", "confirm": "待审核", 'pending': "审核中", "faild": "审核失败",
                    'reviewing': "评审中", "online": "已发布", "preheating": "预热中", "completed": "已完成", "stopped":
                        "已截止", "deleted": "已删除"},
            reward_type={"1": "推荐奖", "2": "团队奖"},
            notice=Notice(),

            weburl="http://127.0.0.1:8000",
            develop_env="true",
            session_secret="3cdcb1f00803b6e78ab50b466a40b9977db396840c28307f428b25e2277f1bcc",
            session_timeout=1800,
            store_options={
                'redis_host': '127.0.0.1',
                'redis_port': 6379,
                'redis_pass': '',
            },
        )

        self.settings = settings
        tornado.web.Application.__init__(self, handlers, ui_modules=ui_modules, **settings)
        self.session_manager = SessionManager(settings["session_secret"], settings["store_options"],
                                              settings["session_timeout"])


if __name__ == "__main__":
    tornado.options.parse_command_line()
    max_buffer_size = 4 * 1024 ** 3  # 4GB
    app = Application()
    # sentry client
    # app.sentry_client = AsyncSentryClient(
    #     'http://9998b9254fa94d5ab6e7a1ee39a0aaa6:492a5997987c42b8be1c44541b1d2a93@120.25.105.117:9000/1')
    # print options.develop
    if not options.develop:
        from config import production

        app.settings.update(production.config)
    else:
        from config import develop

        app.settings.update(develop.config)

    http_server = HTTPServer(
        app,
        max_buffer_size=max_buffer_size,
    )
    # app.listen(options.port, xheaders=True)
    http_server.listen(options.port)
    print "visit at", "http://127.0.0.1:%s" % options.port
    tornado.ioloop.IOLoop.instance().start()
    # 生成20个游客帐号
    # r = _connect_redis()
    # for i in range(1, 5):
    #     r.set("youke"+str(1), 1)
