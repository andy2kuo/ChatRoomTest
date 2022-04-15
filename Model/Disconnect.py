from Model.OperationCode import OperationCode
from Package.Packer import Packer


class DisconnectRequest(object):
    def __init__(self):
        pass

    @staticmethod
    def pack():
        return Packer.pack(OperationCode.OP_DISCONNECT, '')
