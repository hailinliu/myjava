# encoding:utf-8
import requests

# 服务地址
host = "yunpian.com"
# 端口号
port = 80
# 版本号
version = "v1"
# 查账户信息的URI
user_get_uri = "/" + version + "/user/get.json"
# 通用短信接口的URI
sms_send_uri = "/" + version + "/sms/send.json"
# 模板短信接口的URI
sms_tpl_send_uri = "/" + version + "/sms/tpl_send.json"

# apikey
apikey = "1d3f6b7def6125c47d56583116fd938b"

def get_tpl():
    """获取消息模板"""
    url = "http://yunpian.com/v1/tpl/get.json"
    params = {"apikey": apikey}
    r = requests.post(url, files=[], data=params)
    print  r.text


def add_tpl(tpl_content="您的验证码是#code#【蝌蚪网】"):
    """添加消息模板"""
    url = "http://yunpian.com/v1/tpl/get.json"
    params = {
        "apikey": apikey,
        "tpl_content": tpl_content,
        "notify_type": 0
    }
    r = requests.post(url, files=[], data=params)
    print  r.text
