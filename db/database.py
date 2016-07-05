# -*- coding: utf-8 -*-
from pymongo import Connection


class database():
    # conn = Connection('120.25.145.142')
    conn = Connection('127.0.0.1')
    # conn = Connection('mongodb://test:test@120.25.145.142:27017/admin',27017)
    db = conn['weikefarm']
    # db.authenticate("test", "test")

    @classmethod
    def getDB(cls):
        return cls.db
