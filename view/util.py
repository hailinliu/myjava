# encoding:utf-8
import json
import random
import string
import urllib
import urllib2
from BaseHandler import BaseHandler
from verify_code import make as make_verify_code

# 图形验证码
class VerifyCode(BaseHandler):
    def get(self):
        verify_code = ''.join(random.sample(string.ascii_lowercase + string.digits, 4))
        self.set_secure_cookie("verify_code", verify_code)
        content = make_verify_code(verify_code)
        self.set_header('Content-Type', 'image/jpeg;charset=utf-8')
        self.write(content)


# 手机验证码
class SendCode(BaseHandler):
    def post(self):
        mobile_number = self.get_argument("mobile_number")
        msg_code = random.randint(100000, 999999)
        self.set_cookie('msg_code', str(msg_code))
        print self.get_cookie('msg_code')
        url = 'http://yunpian.com/v1/sms/tpl_send.json'
        values = {'apikey': '1d3f6b7def6125c47d56583116fd938b',
                  'mobile': mobile_number,
                  'tpl_id': '908659',
                  'tpl_value': "#code#=%s" % msg_code,
                  }
        data = urllib.urlencode(values)
        req = urllib2.Request(url, data)
        response = urllib2.urlopen(req)
        the_page = response.read()
        self.write(json.dumps(the_page))
