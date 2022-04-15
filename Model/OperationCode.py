from enum import Enum


class OperationCode(Enum):
    OP_PING = 0
    OP_LOGIN = 1
    OP_REGISTER = 2
    OP_GET_CHAT_ROOM_LIST = 3
    OP_SEND_MESSAGE = 4
    OP_DISCONNECT = 5
    OP_LEAVE_ROOM = 6
    OP_JOIN_ROOM = 7
    OP_SYNC_MESSAGE = 8
    OP_RECEIVE_MESSAGE = 9
    OP_KICK_OUT = 10

