#!/usr/bin/env python
# coding: UTF-8
import json
import logging
import re
import time
import datetime

from fabric.api import run, env, cd
import os
from fabric.operations import get
from passlib.handlers.pbkdf2 import pbkdf2_sha512

from db import database

# env.hosts = ['root@49.213.9.157:22']
# env.password = 'TESTWSShc123'

env.hosts = ['root@120.25.145.142:22']
env.password = 'TESTWSShc123'


def test():
    "test"
    run('ls -l /webapps')


def zipdb():
    """
    打包服务器数据文件
    mongodb:kedou
    """
    with cd('/root/work/mongo'):
        run('zip kedou_mongodb.zip kedou.ns kedou.0')


def getzipdb():
    """下载服务器用户上传图片资源文件
    本地存储路径：'../zip/' """
    with cd('/root/work/mongo'):
        get('kedou_mongodb.zip', 'zip/')



def getimagezip():
    """下载服务器用户上传图片资源文件
    本地存储路径：'../zip/' """
    with cd('/webapps/kedou/static/media'):
        get('media.tar.gz', 'zip/')


def test_deploy():
    """测试前后端部署:
    测试端口：7000
    python Main.py --port=7000
    """
    # TODO
    with cd('/webapps/wss_test'):
        run('git reset --hard HEAD')
        run('git pull -f wss wss_test')
        run('sudo supervisorctl restart wss_test')


def restart_web():
    """重启web进程"""
    # TODO
    with cd('/webapps/kedou'):
        run('sudo supervisorctl stop wss_test')
        run('sudo supervisorctl restart wss')


def front_deploy():
    """前端代码部署"""
    # TODO
    with cd('/webapps/kedou'):
        run('sudo supervisorctl stop wss_test')
        run('sudo supervisorctl restart wss')


def back_deploy():
    """前后端代码部署"""
    # TODO
    # 部署
    with cd('/webapps/wss'):
        run('git reset --hard HEAD')
        run('git pull -f wss master')
        run('sudo supervisorctl restart wss')


def back_deploy2():
    """前后端代码部署 https"""
    # TODO
    # 部署
    with cd('/webapps/kedou'):
        run('git reset --hard HEAD')
        run('git pull -f kedou_https master')
        run('sudo supervisorctl restart wss')


def restart_celery():
    """重启计时任务"""
    # TODO
    with cd('/webapps/kedou'):
        run('sudo supervisorctl restart celeryd')



def push_rollback():
    """远程服务器代码回滚
    git 回滚到上一个版本
    """
    # TODO

def reload_mongodb():
    """重启mongodb"""
    run("sudo service mongod reload")

