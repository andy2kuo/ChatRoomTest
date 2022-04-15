# -*- coding: utf-8 -*-
import json
from datetime import datetime

from Model.OperationCode import OperationCode
from Package.Packer import Packer


# 發送訊息請求
class SendMessageRequest:
    def __init__(self, i_data=None):
        if not i_data:
            self.user_id = 0
            self.user_name = ''
            self.message = ''
        else:
            self.user_id = int(i_data['user_id'])
            self.user_name = str(i_data['user_name'])
            self.message = str(i_data['message'].encode('UTF-8'))

    def json_pack(self):
        return {'user_id': self.user_id,
                'user_name': self.user_name,
                'message': self.message}

    def pack(self):
        json_data = json.dumps(self.json_pack())
        return Packer.pack(OperationCode.OP_SEND_MESSAGE, json_data)


# 接收訊息資料
class ReceiveMessage:
    def __init__(self, i_data=None):
        if not i_data:
            self.id = 0
            self.is_system = False
            self.user_id = 0
            self.user_name = ''
            self.message = ''
            self.message_time = datetime.utcnow()
        else:
            self.id = int(i_data['id'])
            self.is_system = bool(i_data['is_system'])
            self.user_id = int(i_data['user_id'])
            self.user_name = str(i_data['user_name'])
            self.message = str(i_data['message'].encode('UTF-8'))
            self.message_time = datetime.strptime(str(i_data['message_time'].encode('UTF-8')), '%Y-%m-%dT%H:%M:%S.000Z')
            # self.message_time = str(i_data['message_time'].encode('UTF-8'))

    def json_pack(self):
        return {'id': self.id,
                'is_system': self.is_system,
                'user_id': self.user_id,
                'user_name': self.user_name,
                'message': self.message,
                'message_time': self.message_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')}

    def pack(self):
        json_data = json.dumps(self.json_pack())
        return Packer.pack(OperationCode.OP_RECEIVE_MESSAGE, json_data)


class SyncMessage(object):
    def __init__(self, i_data=None):
        self.message_list = []
        if i_data:
            for _info in i_data['message_list']:
                self.message_list.append(ReceiveMessage(i_data=_info))

    def json_pack(self):
        json_message_list = []
        for _room in self.message_list:
            json_message_list.append(_room.json_pack())

        return {'message_list': json_message_list}

    def pack(self):
        json_data = json.dumps(self.json_pack())
        return Packer.pack(OperationCode.OP_SYNC_MESSAGE, json_data)
