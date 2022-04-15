import json
from datetime import datetime


class User(object):
    def __init__(self, i_data=None):
        if not i_data:
            self.id = 0
            self.account = ''
            self.password = ''
            self.display_name = ''
            self.gender = ''
            self.age = 0
            self.location = ''
            self.join_time = datetime.utcnow()
            self.last_login_time = datetime.utcnow()
            self.last_logout_time = datetime.utcnow()
            self.total_login_days = 1
            self.cumulative_login_days = 1
            self.score = 0
        else:
            self.id = int(i_data['id'])
            self.account = str(i_data['account'])
            self.password = str(i_data['password'])
            self.display_name = str(i_data['display_name'])
            self.gender = str(i_data['gender'])
            self.age = int(i_data['age'])
            self.location = str(i_data['location'])
            self.join_time = datetime.strptime(str(i_data['join_time'].encode('UTF-8')), '%Y-%m-%dT%H:%M:%S.000Z')
            self.last_login_time = datetime.strptime(str(i_data['last_login_time'].encode('UTF-8')),
                                                     '%Y-%m-%dT%H:%M:%S.000Z')
            self.last_logout_time = datetime.strptime(str(i_data['last_logout_time'].encode('UTF-8')),
                                                      '%Y-%m-%dT%H:%M:%S.000Z')
            self.total_login_days = int(i_data['total_login_days'])
            self.cumulative_login_days = int(i_data['cumulative_login_days'])
            self.score = int(i_data['score'])

    def json_pack(self):
        return {'id': self.id,
                'account': self.account,
                'password': self.password,
                'display_name': self.display_name,
                'gender': self.gender,
                'age': self.age,
                'location': self.location,
                'join_time': self.join_time.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                'last_login_time': self.last_login_time.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                'last_logout_time': self.last_logout_time.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                'total_login_days': self.total_login_days,
                'cumulative_login_days': self.cumulative_login_days,
                'score': self.score}

    def pack(self):
        return json.dumps(self.json_pack())
