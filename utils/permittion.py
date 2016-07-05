# -*- coding: utf-8 -*-

from db import database
import functools
from urllib import urlencode
import urlparse
import tornado.web
from tornado.web import HTTPError


class Permittion(tornado.web.RequestHandler):

    @classmethod
    def authenticated(self, method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            if not self.session:
                if self.request.method in ("GET", "HEAD"):
                    url = self.get_login_url()
                    if "?" not in url:
                        if urlparse.urlsplit(url).scheme:
                            # if login url is absolute, make next absolute too
                            next_url = self.request.full_url()
                        else:
                            next_url = self.request.uri
                        url += "?" + urlencode(dict(next=next_url))
                    self.redirect(url)
                    return
                raise HTTPError(403)

            return method(self, *args, **kwargs)

        return wrapper

    @classmethod
    def admin_authed(self, method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            if not self.session:
                if self.request.method in ("GET", "HEAD"):
                    url = self.get_admin_login_url()
                    if "?" not in url:
                        if urlparse.urlsplit(url).scheme:
                            # if login url is absolute, make next absolute too
                            next_url = self.request.full_url()
                        else:
                            next_url = self.request.uri
                        url += "?" + urlencode(dict(next=next_url))
                    self.redirect(url)
                    return
                raise HTTPError(403)
            else:
                if self.session['data'].get("role", "") != "superadmin":
                    raise HTTPError(403)
            return method(self, *args, **kwargs)

        return wrapper

    @classmethod
    def jury_authed(self, method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            if not self.session:
                if self.request.method in ("GET", "HEAD"):
                    url = self.get_login_url()
                    if "?" not in url:
                        if urlparse.urlsplit(url).scheme:
                            # if login url is absolute, make next absolute too
                            next_url = self.request.full_url()
                        else:
                            next_url = self.request.uri
                        url += "?" + urlencode(dict(next=next_url))
                    self.redirect(url)
                    return
                raise HTTPError(403)
            else:
                if self.user.get("role", "") != "jury":
                    raise HTTPError(403)
            return method(self, *args, **kwargs)

        return wrapper
