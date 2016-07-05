#!/usr/bin/env python
# coding: UTF-8
import json
import logging
import random
import time
from bson import DBRef, ObjectId
import datetime

from fabric.api import run, env, cd
from passlib.handlers.pbkdf2 import pbkdf2_sha512
import sys

from db import database
import argparse
from utils import random_code


def load_json_data():
    """初始化导入json数据"""
    db = database.database.getDB()


def clean_json_data():
    """清空json数据"""
    db = database.database.getDB()


def clean_data():
    """清空据"""
    db = database.database.getDB()
    confirm = raw_input("please confirm remove a tabale, yes or no:")
    if confirm == 'yes':
        db.news.remove()
    else:
        return False


def create_user():
    """创建用户"""
    correct = False
    db = database.database.getDB()
    while 1:
        username = raw_input("username: ")
        exist_user = db.user.find_one({"uid": username})
        if exist_user:
            print "the user %s is existed" % (username)
        else:
            break
    user = []
    email = raw_input("email: ")
    phone = raw_input("phone: ")
    while not correct:
        pwd = raw_input("password:")
        rpwd = raw_input("confirm password:")
        if pwd == rpwd:
            correct = True
            logging.warn(("a  user registered,name is %s") % (username))
            user = {
                "uid": username,
                "name": username,
                "pwd": pwd,
                "email": email,
                "phone": phone,
                'regtime': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())),
            }
        else:
            print "password not correct,please input again"
    password_hash = pbkdf2_sha512.encrypt(user['pwd'])
    user['pwd'] = password_hash
    record = db.user.find_one({"uid": user['uid']})
    if record is not None:
        logging.warn(("that user name %s had been registered") % (username))
        return False
    db.user.insert(user)


def delete_user():
    """删除用户"""
    db = database.database.getDB()
    username = raw_input("username: ")
    db.user.remove({"uid": username})
    logging.warn("user had been removed")


def create_admin():
    """创建管理员账号"""
    correct = False
    db = database.database.getDB()
    while 1:
        username = raw_input("username: ")
        exist_user = db.user.find_one({"uid": username})
        if exist_user:
            print "the user %s is existed" % (username)
        else:
            break
    user = []
    while not correct:
        pwd = raw_input("password:")
        rpwd = raw_input("confirm password:")
        if pwd == rpwd:
            correct = True
            logging.warn(("a admin user registered,name is %s") % (username))
            user = {
                "uid":"18672196620",
                "username": username,
                "pwd": pwd,
                "phone":"18672196620",
                "safe_pwd": pwd,
                'jinbi':10000,
                'money':100000,
                "role": "superadmin",
                'regtime': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())),
            }
        else:
            print "password not correct,please input again"
    password_hash = pbkdf2_sha512.encrypt(user['pwd'])
    user['pwd'] = password_hash
    record = db.user.find_one({"uid": user['uid']})
    if record is not None:
        logging.warn(("that user name %s had been registered") % (username))
        return False
    db.user.insert(user)


def remove_admin():
    """移除管理员账号"""
    db = database.database.getDB()
    db.user.remove({"role": "superadmin"})
    logging.warn("admin user had been removed")


def print_table():
    """查看所有表名，记录数"""
    db = database.database.getDB()
    for d in db.collection_names():
        print "name:%s,count:%d" % (d, db[d].find().count())


def remove_record():
    """移除指定表所有记录"""
    db = database.database.getDB()
    table = raw_input("please input table name:")
    if table in db.collection_names():
        print "%s records count:%d" % (table, db[table].find().count())
        print "remove all record..."
        db[table].remove()
        print "all record are removed,count:%d " % (db[table].find().count())
    else:
        print "not find table named %s" % table

def rollback_award_day():
    """回退分红结算日期一天"""
    db = database.database.getDB()
    back_date = raw_input("turn to date:")
    now_date=str(datetime.datetime.now().date())
    pets=db.my_pet.find({"check_day":now_date})
    for p in pets:
        db.my_pet.update({"check_day":now_date},{"$set":{"check_day":back_date}})

def update_record():
    """更新记录"""
    pass


def delete_project():
    """删除项目相关的所有记录
    project,follow_project,

    """
    db = database.database.getDB()
    projects = db.project.find()
    for p in projects:
        db.follow_project.remove({"ref": DBRef('project', p["_id"])})


def backup_record():
    """备份"""
    print "test"


if __name__ == "__main__":
    # method = sys.argv[1]
    # methods = {"create_admin": create_admin(), "delete_user": delete_user(), "remove_admin": remove_admin()}
    input("please input a method: ")
    # methods.get(method)
