# -*- coding: utf-8 -*-
import sys

from LobbyConnector import LobbyConnector
from ChatUserListener import ChatUserListener
from Database.DatabaseConnect import DatabaseConnect
from Database.RedisConnect import RedisConnector


# 聊天室主控模組
class ChatRoom:
    def __init__(self):
        self.__redis_conn = RedisConnector()
        self.__db_conn = DatabaseConnect()

        self.__user_listener = ChatUserListener(self.__redis_conn, self.__db_conn)
        self.__lobby_connector = LobbyConnector()
        self.__lobby_connector.on_register_response = self.__user_listener.set_server_info
        self.__lobby_connector.get_server_info = self.__user_listener.get_server_info
        self.__lobby_connector.check_duplicate_user = self.__user_listener.check_duplicate_user

    def start(self):
        self.__lobby_connector.connect()


reload(sys)
sys.setdefaultencoding("utf-8")

if __name__ == '__main__':
    # 實例化新的聊天室
    _chat_room = ChatRoom()
    _chat_room.start()
