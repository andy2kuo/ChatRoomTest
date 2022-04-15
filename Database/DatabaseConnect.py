# -*- coding: utf-8 -*-
import datetime as dt

import pymongo

from pymongo import MongoClient

from Model.SendMessageRequest import ReceiveMessage
from Model.User import User
from RedisConnect import RedisConnector


# MongoDB連接器


class DatabaseConnect:
    def __init__(self):
        self.__db_name = 'chat_room_db'
        self.__user_collection_name = 'user'
        self.__config_collection_name = 'config'
        self.__chat_room_collection_name = 'chat_room'
        self.__client = MongoClient('localhost', 27017, max_pool_size=5)

        self.__expire_time = 1

        _collections = self.__client[self.__db_name].collection_names()

        # 如果用戶資料表不存在就創建
        if self.__user_collection_name not in _collections:
            print 'create user collection'
            self.__client[self.__db_name].create_collection(name=self.__user_collection_name)
            self.__client[self.__db_name][self.__user_collection_name].create_index(
                [('id', pymongo.ASCENDING), ('account', pymongo.ASCENDING)],
                unique=True)

        # 如果設定資料表不存在就創建
        if self.__config_collection_name not in _collections:
            print 'create config collection'
            self.__client[self.__db_name].create_collection(name=self.__config_collection_name)
            self.__client[self.__db_name][self.__config_collection_name].insert_one({'id': 0, 'user_id_index': 1})

        # 如果聊天紀錄資料表不存在就創建
        if self.__chat_room_collection_name not in _collections:
            print 'create chat_room collection'
            self.__client[self.__db_name].create_collection(name=self.__chat_room_collection_name)
            self.__client[self.__db_name][self.__chat_room_collection_name].create_index(
                [('msg_id', pymongo.ASCENDING)],
                unique=True)
            self.__client[self.__db_name][self.__chat_room_collection_name].create_index(
                [('msg_expire_time', pymongo.DESCENDING)],
                expireAfterSeconds=0)
            self.__client[self.__db_name][self.__chat_room_collection_name].create_index(
                [('room_name', pymongo.ASCENDING), ('msg_time', pymongo.DESCENDING)])

    # 取得用戶最大ID
    def get_max_user_id(self):
        user_collection = self.__client[self.__db_name][self.__user_collection_name]
        response = user_collection.find().sort([('id', pymongo.ASCENDING)]).limit(1)

        if response:
            if response.count() > 0:
                return int(response[0]['id'])
            else:
                print 'no user exist'
                return 0
        else:
            return 0

    # 新增帳號
    def add_account(self, register_request):
        user_collection = self.__client[self.__db_name][self.__user_collection_name]

        if self.check_acc_exist(register_request.account):
            return False, None

        new_id = self.get_now_user_id()
        new_user = register_request.export_new_user(new_id)
        response = user_collection.insert_one({'id': new_user.id,
                                               'account': new_user.account,
                                               'password': new_user.password,
                                               'display_name': new_user.display_name,
                                               'gender': new_user.gender,
                                               'age': new_user.age,
                                               'location': new_user.location,
                                               'join_time': new_user.join_time,
                                               'last_login_time': new_user.last_login_time,
                                               'last_logout_time': new_user.last_logout_time,
                                               'total_login_days': new_user.total_login_days,
                                               'cumulative_login_days': new_user.cumulative_login_days,
                                               'score': new_user.score})

        if response.acknowledged:
            return True, new_user
        else:
            return False, None

    # 取得目前用戶流水號
    def get_now_user_id(self):
        config_collection = self.__client[self.__db_name][self.__config_collection_name]

        response = config_collection.find_and_modify(query={'id': 0}, update={'$inc': {'user_id_index': 1}})

        return response['user_id_index']

    # 新增訊息紀錄
    def add_message(self, _room_name, _message):
        msg_collection = self.__client[self.__db_name][self.__chat_room_collection_name]

        _expire_delta = dt.timedelta(minutes=self.__expire_time)
        new_msg = {'room_name': _room_name, 'msg_id': _message.id, 'msg_content': _message.message,
                   'msg_user_name': _message.user_name, 'msg_is_sys': _message.is_system,
                   'msg_user_id': _message.user_id, 'msg_time': _message.message_time,
                   'msg_expire_time': _message.message_time + _expire_delta}
        response = msg_collection.insert_one(new_msg)

        if response.acknowledged:
            return True
        else:
            return False

    # 取得指定房間訊息紀錄
    def get_room_messages(self, _room_name):
        msg_collection = self.__client[self.__db_name][self.__chat_room_collection_name]
        response_list = msg_collection.find({'room_name': _room_name}).sort([('msg_time', pymongo.DESCENDING)])\
            .limit(50)

        msg_list = []
        for response in response_list:
            _msg = ReceiveMessage()
            _msg.id = response['msg_id']
            _msg.is_system = response['msg_is_sys']
            _msg.user_id = response['msg_user_id']
            _msg.user_name = response['msg_user_name']
            _msg.message = response['msg_content']
            _msg.message_time = response['msg_time']
            msg_list.append(_msg)

        return msg_list

    # 新增複數帳號
    def add_many_account(self, i_accounts):
        user_collection = self.__client[self.__db_name][self.__user_collection_name]

        response = user_collection.insert_many(i_accounts)

    # 取得帳號
    def get_account(self, account):
        user_collection = self.__client[self.__db_name][self.__user_collection_name]

        response = user_collection.find_one({'account': account})
        if response:
            _user = User()
            _user.id = response['id']
            _user.account = response['account']
            _user.password = response['password']
            _user.display_name = response['display_name']
            _user.gender = response['gender']
            _user.age = response['age']
            _user.location = response['location']
            _user.join_time = response['join_time']
            _user.last_login_time = response['last_login_time']
            _user.last_logout_time = response['last_logout_time']
            _user.total_login_days = response['total_login_days']
            _user.cumulative_login_days = response['cumulative_login_days']
            _user.score = response['score']
            return _user
        else:
            return None

    # 更新會員積分
    def update_user_score(self, _user_id, _bonus):
        user_collection = self.__client[self.__db_name][self.__user_collection_name]

        response = user_collection.find_and_modify(query={'id': _user_id}, update={'$inc': {'score': _bonus}}, new=True)
        return response['score']

    # 更新最後登入資訊
    def update_last_login_info(self, _user_id, _login_time, _cumulative_day, _total_days):
        user_collection = self.__client[self.__db_name][self.__user_collection_name]

        response = user_collection.update_one(
            {
                'id': _user_id
            },
            {
                '$set':
                    {
                        'last_login_time': _login_time
                    },
                '$inc':
                    {
                        'cumulative_login_days': _cumulative_day,
                        'total_login_days': _total_days
                    }
            }
        )
        return response.acknowledged

    # 更新最後登出時間
    def update_last_logout_time(self, _user_id):
        user_collection = self.__client[self.__db_name][self.__user_collection_name]

        response = user_collection.update_one(
            {'id': _user_id},
            {'$set': {'last_logout_time': dt.datetime.utcnow()}})
        return response.acknowledged

    # 檢查帳號是否存在
    def check_acc_exist(self, account):
        user_collection = self.__client[self.__db_name][self.__user_collection_name]

        return user_collection.find_one({'account': account}) is not None


if __name__ == '__main__':
    _redis = RedisConnector()
    _db = DatabaseConnect()
    print _db.get_now_user_id()
