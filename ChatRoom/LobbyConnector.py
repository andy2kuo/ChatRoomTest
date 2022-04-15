# -*- coding: utf-8 -*-
import threading
import time
import socket

from Model.S2S import *
from Package.Packer import Packer


class LobbyConnector:
    def __init__(self):
        self.__conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.address = 'localhost'
        self.port = 9998
        self.__is_connect = False
        self.__reconnect_count = 0
        self.__temp_data = ''
        self.now_request_code = -1
        self.__total_data_count = -1
        self.__update_time = time.clock()
        self.__packer = Packer()

        self.__is_registered = False

        self.on_register_response = None
        self.get_server_info = None
        self.check_duplicate_user = None

        self.__operation_thread = threading.Thread()

    def connect(self):
        try:
            self.__conn.connect((self.address, self.port))
            self.__conn.setblocking(False)
            self.__is_connect = True
            self.__reconnect_count = 0
            self.__operation_thread = threading.Thread(target=self.update)
            self.__operation_thread.start()

        except Exception as e:
            print "error connect", e
            self.__is_connect = False

    def update(self):
        while self.__is_connect:
            # noinspection PyBroadException
            try:
                _request_data = self.__conn.recv(1024)
                self.__packer.add_data(_request_data)
            except:
                pass

            # 處理收到的數據
            while self.__packer.process():
                _code, _package_data = self.__packer.get_package()
                _is_send, _send_package = self.__get_response(_code, _package_data)
                if _is_send:
                    self.__conn.send(_send_package)

            # 已註冊完畢，每經過一秒向大廳更新目前使用人數
            if time.clock() - self.__update_time > 1:
                self.__update_time = time.clock()
                if self.__is_registered:
                    self.__update_info_to_lobby()
                else:
                    self.__register()

    # 處理回覆封包
    def __get_response(self, _code, _package_data):
        if _code == S2SCode.S2S_REGISTER:
            _response = S2SRegisterInfo(i_data=json.loads(str(_package_data)))
            if self.on_register_response:
                self.__is_registered = True
                self.on_register_response(_response)
        elif _code == S2SCode.S2S_UPDATE_SERVER_INFO:
            _request = S2SServerInfo(i_data=json.loads(str(_package_data)))
            if self.get_server_info:
                _name, _count = self.get_server_info()
                _request.name = _name
                _request.user_count = _count
                return True, _request.pack()
        elif _code == S2SCode.S2S_CHECK_DUPLICATE:
            _request = S2SCheckDuplicate(i_data=json.loads(str(_package_data)))
            if self.check_duplicate_user:
                self.check_duplicate_user(_request.user_uid, _request.user_id)

        return False, ''

    # 向大廳取得註冊資訊
    def __register(self):
        _request = S2SRegisterInfo()
        self.__conn.send(_request.pack())

    # 向大廳更新目前伺服器人數
    def __update_info_to_lobby(self):
        _request = S2SServerInfo()
        _request.name, _request.user_count = self.get_server_info()
        self.__conn.send(_request.pack())
