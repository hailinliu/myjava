# coding: utf-8
from __future__ import division
import os
import random
import sys
import time

# 将project目录加入sys.path
from bson import ObjectId
import pymongo

project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_path)

from db import database

from datetime import datetime, timedelta
import datetime
from celery import Celery

import celery_config

app = Celery('wss', backend="amqp", include=['celery_files.celery_tasks'])
app.config_from_object(celery_config)
db = database.database.getDB()

award_setting = db.setting.find_one({"type": 3})


@app.task
def test(x, y):
    """test"""
    print x + y
    return x + y


@app.task
def cal_interests():
    """
    利息结算 从数据库加载setting配置信息
    默认为排期金额的5%
    利息计算时间：8:00~10:00之前排期的，利息从当天算，10点之后排期，则利息从第二天开始计算。
    写入对应的利息结算记录
    """
    today = time.strftime("%Y-%m-%d")
    now_time = str(datetime.datetime.now())
    yesterday = datetime.datetime.today() - timedelta(days=1)
    my_pets = db.my_pet.find({"dead": {"$ne": 1}})
    yesterday_date = yesterday.date()
    day_income = 0
    for p in my_pets:
        info = {}
        uid = p.get("uid")
        print uid
        pid = p.get("pid")
        pet = db.pet.find_one({"id": pid})
        day_jinbi = pet.get("day_jinbi", 0)
        gain = day_jinbi
        life = pet.get('life')
        now_time = datetime.datetime.now().date()
        buy_time = p.get("time")
        b = datetime.datetime.strptime(buy_time, '%Y/%m/%d %H:%M:%S').date()
        live_days = (now_time - b).days
        print "live_days,{}".format(live_days)
        print "check_days,{}".format(p.get("check_day"))
        check_day = str(yesterday_date)
        if live_days > life:
            info.update({"dead": 1})
            db.my_pet.update({"_id": ObjectId(p['_id'])}, {"$set": info})
            continue
        if live_days == 0:
            check_day = str(now_time)
        if p.get("check_day") != check_day:
            if live_days > life:
                info.update({"dead": 1})
                continue
            if live_days == 0:
                producted_jinbi = 1 * day_jinbi
            else:
                producted_jinbi = live_days * day_jinbi
            life_day = p.get("life_day", 0) + 1
            info.update(
                {"gain": gain, "check_day": check_day, "life_day": life_day, "producted_jinbi": producted_jinbi})
            db.my_pet.update({"_id": ObjectId(p['_id'])}, {"$set": info})
            last_trade_log = db.jinbi.find().sort("id", pymongo.DESCENDING).limit(1)
            if last_trade_log.count() > 0:
                lastone = dict()
                for item in last_trade_log:
                    lastone = item
                trade_log_id = int(lastone.get('id', 0)) + 1
            else:
                trade_log_id = 1
            # 写入金币收入记录
            create_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
            db.jinbi.insert({"id": trade_log_id, "type": 'pet_produce', 'money': gain, "uid": uid, "pet_id": pid,
                             "time": str(create_time)})
            db.user.update({"uid": uid}, {"$inc": {"jinbi": gain}})

            user = db.user.find_one({"uid": uid}, {"_id": 0})

            # 计算用户当日累计分红
            if user:
                income_day = check_day
                if 'day_income' not in user:
                    day_income = gain
                else:
                    day_income += gain
                db.user.update({"uid": uid}, {"$set": {"income_day": income_day}})
                db.user.update({"uid": uid}, {"$set": {"day_income": day_income}})
    print "day_income: {}".format(day_income)


@app.task
def cal_manage_award():
    """分红奖"""
    yesterday = datetime.datetime.today() - timedelta(days=1)
    yesterday_date = str(yesterday.date())

    # 获取 购买礼包的用户的昨日分红总额
    users = db.user.find({"income_day": yesterday_date}, {"_id": 0})
    award_percent = [10, 7, 5, 3, 1]
    consume_id = 1
    for u in users:
        user = u
        old_uid = u.get("uid")
        for per in award_percent:
            day_income = u.get('day_income', 0)
            # 查询上级
            admin_id = user.get("admin")
            admin_user = db.user.find_one({"uid": admin_id})
            now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
            if admin_user:
                # id自增1
                last = db.jinbi.find().sort("id", pymongo.DESCENDING).limit(1)
                if last.count() > 0:
                    lastone = dict()
                    for item in last:
                        lastone = item
                    consume_id = int(lastone.get('id', 0)) + 1
                print "admin_id {0},{1}".format(admin_id, day_income * per / 100)
                reward = day_income * per / 100
                if reward != 0:
                    db.jinbi.insert(
                        {"uid": admin_id, "type": "admin_award", "id": consume_id, "time": now_time,
                         "money": reward})
                    db.user.update({"uid": admin_id}, {"$inc": {"jinbi": reward}})
                user = admin_user
        db.user.update({"uid": old_uid}, {"$set": {"day_income": 0}})
        db.user.update({"uid": old_uid}, {"$unset": {'income_day': 1}})

    db.user.update({"day_income": {"$ne":0}}, {"$set": {"day_income": 0}},upsert=True)
    db.user.update({"income_day": {"$exists":True}}, {"$unset": {'income_day': 1}},upsert=True)
@app.task
def test_cal_interests():
    """
    利息结算 从数据库加载setting配置信息
    默认为排期金额的5%
    利息计算时间：8:00~10:00之前排期的，利息从当天算，10点之后排期，则利息从第二天开始计算。
    写入对应的利息结算记录
    """
    today = time.strftime("%Y-%m-%d")
    now_time = str(datetime.datetime.now())
    yesterday = datetime.datetime.today() - timedelta(days=1)
    my_pets = db.my_pet.find({"uid": "13777770004", "dead": {"$ne": 1}})
    yesterday_date = yesterday.date()
    day_income = 0
    for p in my_pets:
        info = {}
        uid = p.get("uid")
        print uid
        pid = p.get("pid")
        pet = db.pet.find_one({"id": pid})
        day_jinbi = pet.get("day_jinbi", 0)
        gain = day_jinbi
        life = pet.get('life')
        now_time = datetime.datetime.now().date()
        buy_time = p.get("time")
        b = datetime.datetime.strptime(buy_time, '%Y/%m/%d %H:%M:%S').date()
        live_days = (now_time - b).days
        print "live_days,{}".format(live_days)
        print "check_days,{}".format(p.get("check_day"))
        check_day = str(yesterday_date)
        if live_days > life:
            info.update({"dead": 1})
        if live_days == 0:
            check_day = str(now_time)
        if p.get("check_day") != check_day:
            if live_days > life:
                info.update({"dead": 1})
                continue
            if live_days == 0:
                producted_jinbi = 1 * day_jinbi
            else:
                producted_jinbi = live_days * day_jinbi
            life_day = p.get("life_day", 0) + 1
            info.update(
                {"gain": gain, "check_day": check_day, "life_day": life_day, "producted_jinbi": producted_jinbi})
            db.my_pet.update({"_id": ObjectId(p['_id'])}, {"$set": info})
            last_trade_log = db.jinbi.find().sort("id", pymongo.DESCENDING).limit(1)
            if last_trade_log.count() > 0:
                lastone = dict()
                for item in last_trade_log:
                    lastone = item
                trade_log_id = int(lastone.get('id', 0)) + 1
            else:
                trade_log_id = 1
            # 写入金币收入记录
            create_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
            db.jinbi.insert({"id": trade_log_id, "type": 'pet_produce', 'money': gain, "uid": uid, "pet_id": pid,
                             "time": str(create_time)})
            db.user.update({"uid": uid}, {"$inc": {"jinbi": gain}})

            user = db.user.find_one({"uid": uid}, {"_id": 0})

            # 计算用户当日累计分红
            if user:
                income_day = check_day
                if 'day_income' not in user:
                    day_income = gain
                else:
                    day_income += gain
                db.user.update({"uid": uid}, {"$set": {"income_day": income_day}})
                db.user.update({"uid": uid}, {"$set": {"day_income": day_income}})
    print "day_income: {}".format(day_income)


@app.task
def test_cal_manage_award():
    """分红奖"""
    yesterday = datetime.datetime.today() - timedelta(days=1)
    yesterday_date = str(yesterday.date())
    # 获取 购买礼包的用户的昨日分红总额
    users = db.user.find({"uid": '13777770004'}, {"_id": 0})
    award_percent = [10, 7, 5, 3, 1]
    consume_id = 1
    for u in users:
        user = u
        old_uid = u.get("uid")
        for per in award_percent:
            day_income = u.get('day_income', 0)
            # 查询上级
            admin_id = user.get("admin")
            admin_user = db.user.find_one({"uid": admin_id})
            now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
            if admin_user:
                # id自增1
                last = db.jinbi.find().sort("id", pymongo.DESCENDING).limit(1)
                if last.count() > 0:
                    lastone = dict()
                    for item in last:
                        lastone = item
                    consume_id = int(lastone.get('id', 0)) + 1
                print ("admin_id {0},{1}").format(admin_id, day_income * per / 100)
                reward = day_income * per / 100
                if reward != 0:
                    db.jinbi.insert(
                        {"uid": admin_id, "type": "admin_award", "id": consume_id, "time": now_time,
                         "money": reward})
                db.user.update({"uid": admin_id}, {"$inc": {"jinbi": reward}})
                user = admin_user
        db.user.update({"uid": old_uid}, {"$set": {"day_income": 0}})
        db.user.update({"uid": old_uid}, {"$unset": {'income_day': 1}})
