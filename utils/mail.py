# encoding:utf-8
import requests

from BaseHandler import BaseHandler


class MailHandler(BaseHandler):
    def send_mail(self, mail_add, sub, content):
        """
        发送邮件
        to_list：收件人；sub：主题；content：邮件内容
        """
        url = "https://sendcloud.sohu.com/webapi/mail.send.json"
        params = {"api_user": self.settings.get("sendcloud_api_user"),
                  "api_key": self.settings.get("sendcloud_api_key"),
                  "to": mail_add,
                  "from": "postmaster@vchits.com",
                  "fromname": "蝌蚪网",
                  "subject": sub,
                  "html": content,
                  "resp_email_id": "true",
                  }
        r = requests.post(url, files=[], data=params)
        print r.text

    def send_chekemail(self, template_invoke_name, substitution_vars):
        """
        发送认证邮件
        sendee：收件人；
        template_invoke_name:模版名称；
        substitution_vars：模板替换变量；
        如: {"to": ["ben@ifaxin.com", "joe@ifaxin.com"],"sub":{"%name%": ["Ben", "Joe"],"%money%":[288, 497]}}
        """
        url = "http://sendcloud.sohu.com/webapi/mail.send_template.json"
        params = {"api_user": self.settings.get("sendcloud_api_user"),
                  "api_key": self.settings.get("sendcloud_api_key"),
                  "from": "postmaster@vchits.com",
                  "fromname": "蝌蚪网",
                  "resp_email_id": "true",
                  "template_invoke_name": template_invoke_name,
                  "substitution_vars": substitution_vars,
                  "gzip_compress": "true",
                  "use_maillist": "false"
                  }
        r = requests.post(url, files=[], data=params)
        print r.text
        return r.json()

    def send_signup_mail(self, user):
        """发送账号激活邮件"""
        site_domain = self.settings.get('SITE_DOMAIN')
        sub = "账号激活 - 蝌蚪网"
        new_url = site_domain + "/user/mail_verify?user_id=%d&token=%s" % (user.id, user.token)
        msg_body = "<p>请将下面的链接完整复制到浏览器地址栏，激活您在蝌蚪网的账号：</p>" \
                   + "<p><a href=%s>%s</a></p>" % (new_url, new_url) \
                   + "<p>本邮件由系统发出，请勿回复；如非本人申请，请联系蝌蚪网。</p>"
        self.send_mail(user.email, sub, msg_body)

    def send_mail_to_admin(self, user):
        """
        用户更新资料后，暂时不显示在搜索页面，等待审批，审批完成后才显示
        """
        admin_email = '295164745@qq.com'
        sub = "用户资料审批 - 蝌蚪网"
        msg_body = "<p>用户%s修改了其个人资料</p>" % user.name
        url = self.settings.get('SITE_DOMAIN') + '/user/' + str(user.id)
        admin_url = self.settings.get('SITE_DOMAIN') + '/admin/info_manage'
        msg_body += '<p>[<a href="' + url + '">查看个人资料</a>]</p>'
        msg_body += '<p>[<a href="' + admin_url + '">进入审批页面</a>]</p>'
        self.send_mail(admin_email, sub, msg_body)

    def send_mail_and_message(self, user, content):
        """
        用管理员的身份同时给用户发一条私信和一封邮件
        """
        dialog = self.db.dialogs.find_one({"dialogist_id": user['uid']})
        if not dialog:
            dialog = {"uid": self.user['uid'], "dialogist_id": user['uid'], "is_sponsor": True}
        message = {"content": content, "sender_id": self.user['uid'], "checked": False, "receiver_id": self.user['uid']}
        dialog.update({
            "message": message
        })
        sub = '来自 - 蝌蚪网 - 的问候'
        msg_body = content
        msg_body += '<p><a href="http://www.kdmaker.com/about">关于蝌蚪</a></p>'
        self.send_mail(user.email, sub, msg_body)

    def send_notify_message(user, content):
        pass

    def send_retrieve_pwd_mail(self, user):
        """发送密码找回邮件"""
        sub = "找回密码 - 蝌蚪网"
        new_url = self.settings.get('SITE_DOMAIN') + "/user/check_token?token=%s&email=%s" % (
            user.token, user.email)
        msg_body = "<p>请将下面的链接完整复制到浏览器地址栏，填写您在蝌蚪网的新密码：</p>" \
                   + "<p><a href=%s>%s</a></p>" % (new_url, new_url) \
                   + "<p>本邮件由系统发出，请勿回复；如密码找回非本人申请，请联系蝌蚪网。</p>"
        self.send_mail(user.email, sub, msg_body)

    def send_private_message_mail(self, sender, receiver):
        """发送私信提醒邮件"""
        sub = "私信提醒 - 蝌蚪网"
        sender_title = "评审" if sender.role == "jury" else "投资人"
        check_url = "%s%s" % (self.settings.get('SITE_DOMAIN'), "/user/message/1")
        msg_body = "<p>%s你好！</p>" % receiver.name \
                   + "<p>蝌蚪网的%s%s向您发送了私信, " % (sender_title, sender.name) \
                   + "<a href=%s>点击此处</a>&nbsp;查看。</p>" % check_url \
                   + "<p>本邮件由系统发出，请勿回复；如有疑问，请联系蝌蚪网。</p>"
        self.send_mail(receiver.email, sub, msg_body)
