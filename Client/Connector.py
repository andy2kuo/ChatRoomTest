# -*- coding: utf-8 -*-
# noinspection PyBroadException

import socket
import time
import json

from Model.ChatRoom import SelectChatRoomRequest, SelectChatRoomResponse, JoinChatRoom
from Model.Disconnect import DisconnectRequest
from Model.Login import LoginResponse
from Model.SendMessageRequest import SendMessageRequest, ReceiveMessage, SyncMessage
from Model.OperationCode import OperationCode
from Model.Ping import Ping
from Model.Register import RegisterResponse
from Package.Packer import Packer


class Connector:
    def __init__(self):
        self.__conn = None
        self.address = ''
        self.port = 0
        self.__is_connect = False
        self.__reconnect_count = 0
        self.__temp_data = ''
        self.now_request_code = -1
        self.__total_data_count = -1
        self.on_login_response = None
        self.on_register_response = None
        self.on_get_room_list = None
        self.on_sync_message = None
        self.on_receive_message = None
        self.__temp_ping_time = time.clock() - 1
        self.__temp_ping_id = 0
        self.__temp_ping_dic = dict()
        self.ping = 999
        self.is_fail = False
        self.is_kick_out = False
        self.__packer = Packer()

        self.__is_register_chat_user = False

    def connect(self, addr, port):
        self.address = addr
        self.port = port
        self.__conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # noinspection PyBroadException
        try:
            self.__conn.connect((self.address, self.port))
            self.__conn.setblocking(False)
            self.__is_connect = True
            self.__reconnect_count = 0

        except Exception as e:
            print "error connect", e
            self.__is_connect = False

    def connect_to_chat(self, i_room_info):
        self.disconnect(False)
        self.connect(self.address, i_room_info.port)

    def update(self):
        # noinspection PyBroadException
        try:
            _request_data = self.__conn.recv(1024)
            self.__packer.add_data(_request_data)

        except:
            pass

        # 處理收到的數據
        while self.__packer.process():
            _code, _package_data = self.__packer.get_package()
            _is_send, _send_package = self.get_response(_code, _package_data)
            if _is_send:
                self.__conn.send(_send_package)

        if time.clock() - self.__temp_ping_time > 1:
            # noinspection PyBroadException
            try:
                self.__temp_ping_dic[self.__temp_ping_id] = time.clock()
                _ping_request = Ping()
                _ping_request.id = self.__temp_ping_id
                self.__conn.send(_ping_request.pack())
                self.__temp_ping_id += 1
                self.__temp_ping_time = time.clock()
            except:
                self.ping = int((time.clock() - self.__temp_ping_time) * 1000)
                print 'ping fail'
                pass

        if not self.is_fail and self.ping > 999:
            self.is_fail = True

    # 處理封包回應
    def get_response(self, code, _data):
        # Ping
        if code == OperationCode.OP_PING:
            _ping_response = Ping(i_data=json.loads(str(_data)))
            _last_ping_time = self.__temp_ping_dic.get(_ping_response.id)
            if _last_ping_time:
                self.ping = int((time.clock() - _last_ping_time) * 1000)
                del self.__temp_ping_dic[_ping_response.id]
        # 登入
        elif code == OperationCode.OP_LOGIN:
            _response = LoginResponse(i_data=json.loads(str(_data).encode('utf-8')))
            if self.on_login_response:
                self.on_login_response(_response)
        # 註冊
        elif code == OperationCode.OP_REGISTER:
            _response = RegisterResponse(i_data=json.loads(str(_data).encode('utf-8')))
            if self.on_register_response:
                self.on_register_response(_response)
        # 取得聊天室列表
        elif code == OperationCode.OP_GET_CHAT_ROOM_LIST:
            _response = SelectChatRoomResponse(i_data=json.loads(str(_data).encode('utf-8')))
            if self.on_get_room_list:
                self.on_get_room_list(_response)
        # 同步訊息
        elif code == OperationCode.OP_SYNC_MESSAGE:
            _response = SyncMessage(i_data=json.loads(str(_data).encode('utf-8')))
            if self.on_sync_message:
                self.on_sync_message(_response)
        # 接收訊息
        elif code == OperationCode.OP_RECEIVE_MESSAGE:
            _response = ReceiveMessage(i_data=json.loads(str(_data).encode('utf-8')))
            if self.on_receive_message:
                self.on_receive_message(_response)
        # 加入房間
        elif code == OperationCode.OP_JOIN_ROOM:
            self.__is_register_chat_user = True
            print 'Chat Room Register Success'
        # 剔除房間
        elif code == OperationCode.OP_KICK_OUT:
            self.is_kick_out = True

        return False, None

    # 是否為連線狀態
    def is_connect(self):
        return self.__is_connect

    # 斷線
    def disconnect(self, reconnect=True):
        if reconnect:
            if self.__conn:
                self.__conn.shutdown(socket.SHUT_RDWR)
                self.__conn.close()

            self.__conn = None
            self.__is_connect = False
            self.reconnect()
        else:
            _request = DisconnectRequest()
            self.__conn.send(_request.pack())

            if self.__conn:
                self.__conn.shutdown(socket.SHUT_RDWR)
                self.__conn.close()

            self.__conn = None
            self.__is_connect = False

    # 重新連線
    def reconnect(self):
        print 'try reconnect'
        self.__reconnect_count += 1
        if self.__reconnect_count < 10:
            self.connect(self.address, self.port)

    # 登入
    def login(self, i_request):
        if self.__is_connect:
            try:
                package = i_request.pack()
                self.__conn.send(package)
                return True
            except Exception as e:
                print 'login', e
                return False
        else:
            return False

    # 註冊
    def register(self, i_request):
        if self.__is_connect:
            try:
                package = i_request.pack()
                self.__conn.send(package)
                return True
            except Exception as e:
                print 'register', e
                return False
        else:
            return False

    # 取得房間列表
    def get_room_list(self):
        if self.__is_connect:
            try:
                _request = SelectChatRoomRequest()
                package = _request.pack()
                self.__conn.send(package)
                return True
            except Exception as e:
                print 'get room list', e
                return False
        else:
            return False

    # 同步房間資訊
    def sync_message(self, i_request):
        if self.__is_connect:
            try:
                package = i_request.pack()
                self.__conn.send(package)
                return True
            except Exception as e:
                print 'sync message', e
                return False
        else:
            return False

    # 向聊天室註冊
    def register_to_chat_room(self, i_user_uid, i_user):
        _inter_time = time.clock()

        while not self.__is_register_chat_user:
            if time.clock() - _inter_time >= 2:
                _inter_time = time.clock()

                _request = JoinChatRoom()
                _request.user = i_user
                _request.user_uid = i_user_uid
                package = _request.pack()
                self.__conn.send(package)
                break

    # 發送訊息
    def send_message(self, i_request):
        if self.__is_connect:
            try:
                package = i_request.pack()
                self.__conn.send(package)
                return True
            except Exception as e:
                print 'send message', e
                return False
        else:
            return False
