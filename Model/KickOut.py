import json

from Model.OperationCode import OperationCode
from Package.Packer import Packer


class KickOut(object):
    def __init__(self):
        pass

    @staticmethod
    def json_pack():
        return {}

    def pack(self):
        json_data = json.dumps(self.json_pack())
        return Packer.pack(OperationCode.OP_KICK_OUT, json_data)
