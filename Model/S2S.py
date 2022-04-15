import json
from datetime import datetime

from enum import Enum

from Package.Packer import Packer


class S2SCode(Enum):
    S2S_REGISTER = 0
    S2S_ADD_USER = 1
    S2S_UPDATE_SERVER_INFO = 2
    S2S_CHECK_DUPLICATE = 3


# Server To Server Register
class S2SRegisterInfo:
    def __init__(self, i_data=None):
        if not i_data:
            self.id = 0
            self.name = ''
            self.port = 0
            self.create_time = datetime.utcnow()
        else:
            self.id = int(i_data['id'])
            self.name = str(i_data['name'])
            self.port = int(i_data['port'])
            self.create_time = datetime.strptime(str(i_data['create_time'].encode('UTF-8')), '%Y-%m-%dT%H:%M:%S.000Z')

    def json_pack(self):
        return {'id': self.id, 'name': self.name, 'port': self.port,
                'create_time': self.create_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')}

    def pack(self):
        json_data = json.dumps(self.json_pack())
        return Packer.pack(S2SCode.S2S_REGISTER, json_data)


# Server To Server Get Server Info
class S2SServerInfo:
    def __init__(self, i_data=None):
        if not i_data:
            self.name = ''
            self.user_count = 0
        else:
            self.name = str(i_data['name'])
            self.user_count = int(i_data['user_count'])

    def json_pack(self):
        return {'name': self.name, 'user_count': self.user_count}

    def pack(self):
        json_data = json.dumps(self.json_pack())
        return Packer.pack(S2SCode.S2S_UPDATE_SERVER_INFO, json_data)


# Server To Server Check Duplicate
class S2SCheckDuplicate:
    def __init__(self, i_data=None):
        if not i_data:
            self.user_uid = 0
            self.user_id = ''
        else:
            self.user_uid = str(i_data['user_uid'])
            self.user_id = str(i_data['user_id'])

    def json_pack(self):
        return {'user_id': self.user_id, 'user_uid': self.user_uid}

    def pack(self):
        json_data = json.dumps(self.json_pack())
        return Packer.pack(S2SCode.S2S_CHECK_DUPLICATE, json_data)
