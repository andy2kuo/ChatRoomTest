# -*- coding: utf-8 -*-
import redis


# Redis連接器
class RedisConnector:
    def __init__(self):
        self.ttl_time = 60
        self.__db = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.f_user_now_id = 'user_now_id'

    # 取得最新訊息編號
    def get_next_msg_id(self, _room_name):
        return self.__db.incr(_room_name, 1)
