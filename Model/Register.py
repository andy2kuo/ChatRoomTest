import json
from datetime import datetime

from Model.OperationCode import OperationCode
from Model.User import User
from Package.Packer import Packer


class RegisterRequest(object):
    def __init__(self, i_data=None):
        if not i_data:
            self.account = ''
            self.password = ''
            self.display_name = ''
            self.gender = ''
            self.age = 0
            self.location = ''
            self.last_login_time = datetime.utcnow()
            self.join_time = datetime.utcnow()
        else:
            self.account = str(i_data['account'])
            self.password = str(i_data['password'])
            self.display_name = str(i_data['display_name'])
            self.gender = str(i_data['gender'])
            self.age = int(i_data['age'])
            self.location = str(i_data['location'])
            self.last_login_time = datetime.strptime(str(i_data['last_login_time'].encode('UTF-8')),
                                                     '%Y-%m-%dT%H:%M:%S.000Z')
            self.join_time = datetime.strptime(str(i_data['join_time'].encode('UTF-8')),
                                               '%Y-%m-%dT%H:%M:%S.000Z')

    def export_new_user(self, new_id):
        new_user = User()
        new_user.id = new_id
        new_user.account = self.account
        new_user.password = self.password
        new_user.display_name = self.display_name
        new_user.gender = self.gender
        new_user.age = self.age
        new_user.location = self.location
        new_user.last_login_time = self.last_login_time
        new_user.join_time = self.join_time
        return new_user

    def json_pack(self):
        return {'account': self.account, 'password': self.password, 'display_name': self.display_name,
                'gender': self.gender, 'age': self.age, 'location': self.location,
                'last_login_time': self.last_login_time.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                'join_time': self.join_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')}

    def pack(self):
        json_data = json.dumps(self.json_pack())
        return Packer.pack(OperationCode.OP_REGISTER, json_data)


class RegisterResponse(object):
    def __init__(self, i_data=None):
        if not i_data:
            self.register_result = False
            self.user = User()
        else:
            self.register_result = bool(i_data['register_result'])
            self.user = User(i_data=i_data['user'])

    def json_pack(self):
        return {'register_result': self.register_result, 'user': self.user.json_pack()}

    def pack(self):
        json_data = json.dumps(self.json_pack())
        return Packer.pack(OperationCode.OP_REGISTER, json_data)
