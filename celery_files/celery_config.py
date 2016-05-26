# encoding:utf-8
from celery.schedules import crontab
from celery import platforms
from datetime import timedelta

platforms.C_FORCE_ROOT = True
BROKER_URL = 'redis://localhost'
# BROKER_URL = 'amqp://guest:guest@localhost:5672//'
CELERY_TIMEZONE = 'Asia/Shanghai'
CELERY_ROUTES = {"celery_files.celery_tasks.test": {"queue": "hipri"},
                 "celery_files.celery_tasks.cal_interests": {},
                 }
CELERYBEAT_SCHEDULE = {
    # Executes every midnight at 00:00 A.M
    'plan_test': {
        'task': 'celery_tasks.test',
        'schedule': timedelta(seconds=10),
        # 'schedule':crontab(minute=50, hour=14),
        "args": (4, 4)
    },
    'cal_interests': {
        'task': 'celery_tasks.cal_interests',
        "schedule": crontab(minute=39, hour=20),
        # "schedule": timedelta(seconds=300),
        "args": ()
    },
    'cal_manage_award': {
        'task': 'celery_tasks.cal_manage_award',
        "schedule": crontab(minute=40, hour=20),
        # "schedule": timedelta(seconds=360),
        "args": ()
    },


}

# 添加以下语句到环境变量
# export C_FORCE_ROOT="true"
