# coding: utf-8
from __future__ import division
import os
import random
import sys
import time

# 将project目录加入sys.path
from bson import ObjectId

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
    yesterday_date=yesterday.date()
    for p in my_pets:
        info = {}
        uid = p.get("uid")
        pet_id = p.get("id")
        pid= p.get("pid")
        pet =db.pet.find_one({"id":pid})
        day_jinbi = pet.get("day_jinbi")
        gain = day_jinbi
        life = pet.get('life')
        now_time = datetime.datetime.now()
        buy_time = p.get("time")
        b = datetime.datetime.strptime(buy_time, '%Y/%m/%d %H:%M:%S')
        live_days = (now_time - b).days
        if live_days>0:
            if p.get("check_day") != str(yesterday_date):
                if live_days > life:
                    info.update({"dead": 1})
                producted_jinbi=live_days*day_jinbi
                info.update({"gain": gain, "check_day": str(yesterday_date),"producted_jinbi":producted_jinbi})
                db.my_pet.update({"_id": ObjectId(p['_id'])}, {"$set": info})
                # 写入金币收入记录
                db.jinbi.insert({"type": 'pet_produce', 'money': gain, "uid":uid,"pet_id": pid, "time": str(now_time)})
                db.user.update({"uid": uid}, {"$inc": {"jinbi": gain}})


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
