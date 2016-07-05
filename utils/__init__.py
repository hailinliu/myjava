# encoding:utf-8
import json
import random
import string
import urllib
import urllib2
import datetime

from BaseHandler import BaseHandler
from verify_code import make as make_verify_code


class Singleton(object):
    """单例"""

    def __new__(cls, *args, **kw):
        if not hasattr(cls, '_instance'):
            orig = super(Singleton, cls)
            cls._instance = orig.__new__(cls, *args, **kw)
        return cls._instance


# 图形验证码
class VerifyCode(BaseHandler):
    def get(self):
        verify_code = ''.join(random.sample(string.ascii_lowercase + string.digits, 4))
        self.set_secure_cookie("verify_code", verify_code)
        content = make_verify_code(verify_code)
        self.set_header('Content-Type', 'image/jpeg;charset=utf-8')
        self.write(content)


def send_short_msg(tpl_id='908659', tpl_value="#code#=123456", mobile_number='18672196610'):
    url = 'http://yunpian.com/v1/sms/tpl_send.json'
    values = {'apikey': '0cae3c9d6ecade53a787efabb4a16729',
              'mobile': mobile_number,
              'tpl_id': tpl_id,
              'tpl_value': tpl_value,
              }
    print values
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    return response.read()


def random_code(randomlength=7):
    """生成随机编号"""
    str = ''
    chars = '0123456789'
    length = len(chars) - 1
    obj = random.Random()
    for i in range(randomlength):
        str += chars[obj.randint(0, length)]
    return str


def datediff(beginDate, endDate):
    format = "%Y-%m-%d"
    bd = beginDate
    ed = endDate
    oneday = datetime.timedelta(days=1)
    count = 0
    while bd != ed:
        ed = ed - oneday
        count += 1
    return count
