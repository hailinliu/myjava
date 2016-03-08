import pymongo

from passlib.hash import pbkdf2_sha512
from db.database import database as mongodb


class Authentication:
    def log_in(self, username, password):
        return False

    def log_out(self, username):
        return

    def register(self, username, password, acls):
        return False

    def get_acls(self, username):
        return []

    def has_acl(self, username, acl):
        return False


class MongoAuthentication(Authentication):
    def __init__(self, database, collection):
        # self._conn = pymongo.Connection(**kwargs)
        self._conn = mongodb.conn
        self._coll = self._conn[database][collection]

    def log_in(self, username, password):

        record = self._coll.find_one({"$or": [{'username': username}, {"uid": username}, {'phone': username}]})
        # print username
        if record is None:
            print "user not exist"
            return False
        password_hash = record['pwd']

        rs = pbkdf2_sha512.verify(password, password_hash)
        return rs

    def admin_log_in(self, username, password):

        record = self._coll.find_one({"username": username})
        print username
        if record is None:
            print "user not exist"
            return False
        password_hash = record['pwd']

        rs = pbkdf2_sha512.verify(password, password_hash)
        return rs

    def log_out(self, username):
        return

    def register(self, user):
        if user['uid'] is None or user['pwd'] is None or user['uid'] == "" or \
                        user['pwd'] == "":
            return False

        record = self._coll.find_one({"uid": user['uid']})
        if record is not None:
            return False

        password_hash = pbkdf2_sha512.encrypt(user['pwd'])
        user['pwd'] = password_hash
        self._coll.insert(user)
        return True

    def changepwd(self, uid, newpwd):
        record = self._coll.find_one({"uid": uid})
        if record is None:
            return False
        password_hash = pbkdf2_sha512.encrypt(newpwd)
        if record['pwd'] == password_hash:
            return False
        self._coll.update({'uid': uid}, {'$set': {'pwd': password_hash}})
        return True

    def changephone(self, uid, new_phone):
        record = self._coll.find_one({"uid": uid})
        if record is None:
            return False
        self._coll.update({'uid': uid}, {'$set': {'phone': new_phone}})
        return True

    def changeemail(self, uid, new_email):
        record = self._coll.find_one({"uid": uid})
        if record is None:
            return False
        self._coll.update({'uid': uid}, {'$set': {'email': new_email}})
        return True

    def changepaypwd(self, uid, newpwd):
        record = self._coll.find_one({"uid": uid})
        password_hash = pbkdf2_sha512.encrypt(newpwd)
        if record is None:
            return False
        self._coll.update({'uid': uid}, {'$set': {'pay_pwd': password_hash}})
        return True

    def get_acls(self, username):
        record = self._coll.find_one({"username": username})
        if record is None:
            return []
        return record['acl']

    def has_acl(self, username, acl):
        acls = self.get_acls(username)
        return acl in acls
