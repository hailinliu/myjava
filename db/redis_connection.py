# -*- coding: utf-8 -*-
from datetime import datetime
from redis import Redis
import time


def set_user_active_time(user_id):
    """将此用户标记为online"""
    r = _connect_redis()
    if r:
        user_key = 'user-active:%d' % user_id
        p = r.pipeline()
        p.set(user_key, int(time.time()))
        p.execute()


def get_user_active_time(user_id):
    """获取用户最后登录时间，若不存在则返回None"""
    r = _connect_redis()
    if r:
        user_key = 'user-active:%d' % user_id
        active_time = r.get(user_key)
        if active_time:
            return datetime.fromtimestamp(int(active_time))
        else:
            return None
    else:
        return None


def set_upload_progress(user_id, progress):
    """设置用户上传视频的进度"""
    r = _connect_redis()
    if r:
        user_key = '%s:%d' % (user_id, progress)
        # p = r.pipeline()
        # p.set(user_key, int(time.time()))
        # p.execute()
        r.set("progress", progress)


def get_upload_progress(user_id):
    """获取用户上传视频的进度"""
    r = _connect_redis()
    if r:
        # user_key = '%s:%d' % (user_id, pro)
        # progress = r.get(user_key)
        progress = r.get("progress")
        return progress
    else:
        return 0


class LoginState(object):
    @staticmethod
    def signin(token, user_id):
        r = _connect_redis()
        if r:
            user_key = 'user-token:%s' % token
            p = r.pipeline()
            p.set(user_key, user_id)
            p.execute()

    @staticmethod
    def signout(token):
        r = _connect_redis()
        if r:
            user_key = 'user-token:%s' % token
            p = r.pipeline()
            p.delete(user_key)
            p.execute()

    @staticmethod
    def check_login(token):
        r = _connect_redis()
        if r:
            user_key = 'user-token:%s' % token
            user_id = r.get(user_key)
            if user_id:
                return user_id
            else:
                return -1
        else:
            return -1


def _connect_redis():
    """建立Redis连接"""
    config = {"REDIS": True, "REDIS_HOST": "120.25.105.117", "REDIS_PORT": 6379, "REDIS_DB": 1}
    # config = {"REDIS": True, "REDIS_HOST": "127.0.0.1", "REDIS_PORT": 6379, "REDIS_DB": 1}
    return Redis(host=config.get('REDIS_HOST'), port=config.get('REDIS_PORT'),
                 db=config.get('REDIS_DB'))
