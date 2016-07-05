# encoding:utf-8
import json
import logging
import os
import urllib
import urllib2
import time
from db import database
from utils import Singleton
from BaseHandler import BaseHandler

log_path = os.path.join(os.getcwd(), "log")

log_filename = os.path.join(log_path, "warn.log")
if not os.path.exists(log_filename):
    if os.path.isdir("./log"):
        pass
    else:
        os.mkdir("./log")
    f = open(log_filename, 'w')
    f.close()

logging.basicConfig(level=logging.WARN,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename=log_filename,
                    filemode='w')


class Notice(Singleton):
    """站内通知
        tpye:消息类型
        level:消息级别
        tpl_id:短消息模板id
        timeout:超时未读取发送短信通知
    """

    def __int__(self):
        self.timeout = 60 * 60 * 24

    @property
    def db(self):
        return database.database.getDB()

    def send(self, uid, type, type_id, handle, title, content):
        """
        发送站内信
        type:消息类型
            0: 登录注册
            1：创意审核
            2：项目审核
            3：活动审核
            4. 创意评审
            5. 项目评审
            6. 创意上线
            7. 项目上线
            8. 创意股权计划
            9. 项目股权计划
            10.邀请参与项目评审
            11.股权计划认购完成
            13.创业园审核
            14.公开课审核
            15.入孵创业园
        handle:处理方式
            0：null -->未处理
            1：pass-->通过
            2：failed-->审核失败，拒绝
            3：online-->上线
            4：offline-->下线
            5: deleted-->被删除
            6：invite --> 邀请
            7. agree-->同意
            8.refuse-->拒绝
        """
        self.db.notice.insert(
            {"uid": uid, "type": type, "type_id": type_id, "handle": handle, "title": title, "content": content,
             "unread": 1, "time": time.strftime("%Y-%m-%d %H:%M:%S")})
        self.db.user.update({"uid": uid}, {'$inc': {'unread': 1}})
        logging.info(("send notice to %s,type is %d") % (uid, type))

    def multi_send(self, users, type, type_id, handle, title, content):
        """
        同时发送通知给多个用户:
        邀请评审员参与评审
        """
        for u in users:
            print type
            self.db.notice.insert(
                {"uid": u['uid'], "type": type, "type_id": type_id, "handle": handle, "title": title,
                 "content": content,
                 "unread": 1, "time": time.strftime("%Y-%m-%d %H:%M:%S")})
            logging.info(("send invite notice to %s,type is %d") % (u['uid'], type))

    def read(self, user, id):
        """读取站内信"""
        notice = self.db.notice.find_one({"uid": user['uid'], "id": id})
        notice['unread'] = True
        self.db.notice.update({"uid": user['uid']}, notice)
        logging.info(("%u read notice %d") % (user['name'], id))

    def remove(self, user, id):
        """删除站内信"""
        notice = self.db.notice.find_one({"uid": user['uid'], "id": id})
        if notice:
            notice.remove()
            logging.warn(("notice %d is be deleted,by user %s") % (id, user['name']))

    def timeout_unread(self):
        """消息超时未读"""
        pass

    def get_tpl(self, type):
        """获取消息模板"""
        tpl_id = self.db.message_tpl.find_one({"type": type})
        return tpl_id

    def format_tpl_value(self, type, id):
        """格式化短消息内容"""

        return "#type#=%s&#id#=%s" % (type, id)

    def short_message(self, user, type, id):
        """站内信短信通知"""
        url = 'http://yunpian.com/v1/sms/tpl_send.json'
        values = {'apikey': '1d3f6b7def6125c47d56583116fd938b',
                  'mobile': user['mobile'],
                  'tpl_id': self.get_tpl(type),
                  'tpl_value': self.format_tpl_value(id, type),
                  }
        data = urllib.urlencode(values)
        req = urllib2.Request(url, data)
        response = urllib2.urlopen(req)
        the_page = response.read()
        logging.info(json.dumps(the_page))
