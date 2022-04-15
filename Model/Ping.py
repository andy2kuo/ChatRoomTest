import json

from Model.OperationCode import OperationCode
from Package.Packer import Packer


class Ping(object):
    def __init__(self, i_data=None):
        if not i_data:
            self.id = 0
        else:
            self.id = int(i_data['id'])

    def json_pack(self):
        return {'id': self.id}

    def pack(self):
        json_data = json.dumps(self.json_pack())
        return Packer.pack(OperationCode.OP_PING, json_data)
