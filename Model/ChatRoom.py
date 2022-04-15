# -*- coding: utf-8 -*-
import json
from datetime import datetime

from Model.OperationCode import OperationCode
from Model.User import User
from Package.Packer import Packer


# 加入房間
class JoinChatRoom:
    def __init__(self, i_data=None):
        if not i_data:
            self.user_uid = ''
            self.user = User()
        else:
            self.user_uid = str(i_data['user_uid'])
            self.user = User(i_data=i_data['user'])

    def json_pack(self):
        return {'user': self.user.json_pack(), 'user_uid': self.user_uid}

    def pack(self):
        json_data = json.dumps(self.json_pack())
        return Packer.pack(OperationCode.OP_JOIN_ROOM, json_data)


# 聊天室資訊
class ChatRoomInfo(object):
    def __init__(self, i_data=None):
        if not i_data:
            self.id = ''
            self.name = ''
            self.create_time = datetime.utcnow()
            self.port = 0
            self.now_user_count = 0
            self.limit_user_count = 0
        else:
            self.id = str(i_data['id'])
            self.name = str(i_data['name'])
            self.create_time = datetime.strptime(str(i_data['create_time'].encode('UTF-8')), '%Y-%m-%dT%H:%M:%S.000Z')
            self.port = int(i_data['port'])
            self.now_user_count = int(i_data['now_user_count'])
            self.limit_user_count = int(i_data['limit_user_count'])

    def json_pack(self):
        return {'id': self.id,
                'name': self.name,
                'create_time': self.create_time.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                'port': self.port,
                'now_user_count': self.now_user_count,
                'limit_user_count': self.limit_user_count}

    def pack(self):
        return json.dumps(self.json_pack())


# 取得聊天室列表請求
class SelectChatRoomRequest(object):
    def __init__(self):
        pass

    @staticmethod
    def pack():
        return Packer.pack(OperationCode.OP_GET_CHAT_ROOM_LIST, '')


# 取得聊天室列表請求回應
class SelectChatRoomResponse(object):
    def __init__(self, i_data=None):
        self.chat_room_list = []
        if i_data:
            for _info in i_data['chat_room_list']:
                self.chat_room_list.append(ChatRoomInfo(i_data=_info))

    def json_pack(self):
        json_room_list = []
        for _room in self.chat_room_list:
            json_room_list.append(_room.json_pack())

        return {'chat_room_list': json_room_list}

    def pack(self):
        json_data = json.dumps(self.json_pack())
        return Packer.pack(OperationCode.OP_GET_CHAT_ROOM_LIST, json_data)
