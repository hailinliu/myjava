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
    day_income=0
    for p in my_pets:
        info = {}
        uid = p.get("uid")
        print uid
        pid = p.get("pid")
        pet = db.pet.find_one({"id": pid})
        day_jinbi = pet.get("day_jinbi")
        gain = day_jinbi
        life = pet.get('life')
        now_time = datetime.datetime.now()
        buy_time = p.get("time")
        b = datetime.datetime.strptime(buy_time, '%Y/%m/%d %H:%M:%S')
        live_days = (now_time - b).days
        print "live_days,", live_days
        print "check_days", p.get("check_day")
        #TODO 记得换回来
        # if live_days > 0:
        if 1:
            #TODO 记得换回来
            # if p.get("check_day") != str(yesterday_date):
            if 2:
                if live_days > life:
                    info.update({"dead": 1})
                    continue
                producted_jinbi = live_days * day_jinbi
                #TODO 记得换回来
                producted_jinbi =1 * day_jinbi
                info.update({"gain": gain, "check_day": str(yesterday_date), "producted_jinbi": producted_jinbi})
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
                db.user.update({"uid":uid},{"$inc":{"jinbi":gain}})

                user = db.user.find_one({"uid": uid}, {"_id": 0})

                # 计算用户当日累计分红
                if user:
                    income_day = str(yesterday_date)
                    if 'day_income' not in user:
                        day_income = gain
                    else:
                        day_income += gain
                    db.user.update({"uid": uid}, {"$set": {"income_day": income_day}})
                    db.user.update({"uid": uid}, {"$set": {"day_income": day_income}})


@app.task
def cal_manage_award():
    """分红奖"""
    yesterday = datetime.datetime.today() - timedelta(days=1)
    yesterday_date = str(yesterday.date())

    # 获取 购买红包的用户的昨日分红总额
    users = db.user.find({"income_day": yesterday_date}, {"_id": 0})
    users = db.user.find({"income_day": yesterday_date}, {"_id": 0})
    award_percent = [10, 7, 5, 3, 1]
    consume_id = 1
    for u in users:
        day_income = u.get('day_income', 0)
        user=u
        for per in award_percent:
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
                print admin_id, day_income * per / 100
                reward = day_income * per / 100
                db.jinbi.insert(
                    {"uid": admin_id, "type": "admin_award", "id": consume_id, "time": now_time,
                     "money": reward})
                db.user.update({"uid": admin_id}, {"$inc": {"jinbi": reward}})
                db.user.update({"uid": admin_id}, {"$set": {"day_income": 0}})
                user = admin_user


@app.task
def cal_award():
    """
    奖金计算
    1.查找已完成的未统计奖金的提供帮助记录
    2.查找记录的uid的代理，循环放到字典去。
    3.根据系统设置的奖金比，更新对应层级代理的奖金
    4.插入对应的奖金记录

    """
    helps = db.provide_help.find({"status": "complete", "check_award": {"$ne": "checked"}})
    now_time = str(datetime.datetime.now())
    for h in helps:
        index = 1
        user = db.user.find_one({"uid": h.get("uid")})
        admin_uid = user.get("adin")
        admin = db.user.find_one({"uid": admin_uid})
        jine = h.get("jine", 0)
        award_id = str(time.time()).replace(".", "")[4:]
        award_money = int(jine) * award_setting[str(index)]
        db.user.update({"uid": admin_uid}, {"$set": {"award": admin.get("award", 0) + award_money}})
        db.award.insert(
            {'id': award_id, "uid": admin_uid, "type": str(index), "jine": award_money, "match_money": h.get("jine"),
             "time": now_time})
        admin_id = admin.get("admin")
        while admin_id:
            if index > 12:
                break
            award_id = str(time.time()).replace(".", "")[4:]
            admin = db.user.find_one({"uid": admin_id})
            index += 1
            award_money = h.get("jine") * award_setting[str(index)]
            db.user.update({"uid": admin_uid}, {"$set": {"award": admin.get("award", 0) + award_money}})
            db.award.insert(
                {"id": award_id, "uid": admin_uid, "title": str(index) + "代" + award_setting[str(index)] + "%",
                 "jine": award_money, "match_money": h.get("jine"),
                 "time": now_time})
            admin_id = admin.get("admin")
