import json
from datetime import datetime

from Model.OperationCode import OperationCode
from Model.User import User
from Package.Packer import Packer


class LoginRequest(object):
    def __init__(self, i_data=None):
        if not i_data:
            self.account = ''
            self.password = ''
            self.last_login_time = datetime.utcnow()
        else:
            self.account = str(i_data['account'])
            self.password = str(i_data['password'])
            self.last_login_time = datetime.strptime(str(i_data['last_login_time'].encode('UTF-8')),
                                                     '%Y-%m-%dT%H:%M:%S.000Z')

    def json_pack(self):
        return {'account': self.account,
                'password': self.password,
                'last_login_time': self.last_login_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')}

    def pack(self):
        json_data = json.dumps(self.json_pack())
        return Packer.pack(OperationCode.OP_LOGIN, json_data)


class LoginResponse(object):
    def __init__(self, i_data=None):
        if not i_data:
            self.login_result = 0
            self.user_uid = ''
            self.user = User()
        else:
            self.login_result = int(i_data['login_result'])
            self.user_uid = str(i_data['user_uid'])
            self.user = User(i_data=i_data['user'])

    def json_pack(self):
        return {'login_result': self.login_result, 'user': self.user.json_pack(), 'user_uid': self.user_uid}

    def pack(self):
        json_data = json.dumps(self.json_pack())
        return Packer.pack(OperationCode.OP_LOGIN, json_data)
