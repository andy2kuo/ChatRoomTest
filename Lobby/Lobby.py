# -*- coding: utf-8 -*-
import sys

from ChatRoomS2SListener import ChatRoomS2SListener
from Database.DatabaseConnect import DatabaseConnect
from Database.RedisConnect import RedisConnector
from LobbyListener import LobbyListener

reload(sys)
sys.setdefaultencoding("utf-8")

if __name__ == '__main__':
    __redis_conn = RedisConnector()
    __db_conn = DatabaseConnect()

    # 實例化大廳會員監聽器
    _lobby_listener = LobbyListener(__redis_conn, __db_conn)
    _lobby_listener.start()

    # 實例化大廳聊天室監聽器
    _chat_room_listener = ChatRoomS2SListener(__redis_conn, __db_conn)
    _chat_room_listener.start()

    # 串接接口
    _lobby_listener.get_room_list = _chat_room_listener.get_room_list
    _lobby_listener.check_duplicate = _chat_room_listener.check_duplicate

    # noinspection PyBroadException
    try:
        while _lobby_listener.is_running and _chat_room_listener.is_running:
            pass
    except:
        pass

    _lobby_listener.stop()
    _chat_room_listener.stop()
