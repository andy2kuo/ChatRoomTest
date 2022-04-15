# -*- coding: utf-8 -*-
import json
import socket
import sys
import threading
import time
from datetime import datetime

from Model.ChatRoom import ChatRoomInfo, SelectChatRoomResponse
from Model.S2S import S2SCode, S2SRegisterInfo, S2SServerInfo, S2SCheckDuplicate
from Model.User import User
from Package.Packer import Packer

reload(sys)
sys.setdefaultencoding('utf-8')


# 來自聊天室的連接
class ChatRoomS2SCon:
    def __init__(self, _conn, _db, _redis):
        self.__user = User()
        self.is_connected = True
        self.__conn = _conn
        self.__conn.setblocking(0)
        self.__db = _db
        self.__redis = _redis
        self.__ping_time = time.clock()
        self.__packer = Packer()

        self.client_id = 0
        self.room_name = ''
        self.room_port = 0
        self.create_time = datetime.utcnow()

        self.now_chat_user_count = 0
        self.limit_chat_user_count = 5

    # 接收自聊天室Server的封包
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

        return time.clock() - self.__ping_time <= 3 and self.is_connected

    # 重置Ping確認時間
    def __reset_ping_time(self):
        self.__ping_time = time.clock()

    # 取得房間資訊
    def get_room_info(self):
        _room_info = ChatRoomInfo()
        _room_info.id = self.client_id
        _room_info.name = self.room_name
        _room_info.port = self.room_port
        _room_info.now_user_count = self.now_chat_user_count
        _room_info.limit_user_count = self.limit_chat_user_count

        return _room_info

    # 發送檢查重複登入
    def send_check_duplicate(self, _request):
        print self.room_name, 'check duplicate'
        self.__conn.send(_request.pack())

    # 處理回覆
    def get_response(self, _code, _data):
        self.__reset_ping_time()

        # 註冊處理
        if _code == S2SCode.S2S_REGISTER:
            _response = S2SRegisterInfo(i_data=json.loads(str(_data).encode('utf-8')))
            _response.id = self.client_id
            _response.name = self.room_name
            _response.port = self.room_port
            _response.create_time = self.create_time

            return True, _response.pack()
        # 更新Server資訊
        elif _code == S2SCode.S2S_UPDATE_SERVER_INFO:
            _request = S2SServerInfo(i_data=json.loads(str(_data).encode('utf-8')))

            self.now_chat_user_count = _request.user_count

        return False, None

    # 將客戶端斷線
    def disconnect(self):
        if not self.__user:
            print 'disconnect'
        else:
            print self.__user.display_name, 'disconnect'

        if self.is_connected:
            # noinspection PyBroadException
            try:
                self.__conn.shutdown(socket.SHUT_RDWR)
                self.__conn.close()
            except:
                pass

        self.is_connected = False


# 聊天室與大廳連接監聽器
class ChatRoomS2SListener:
    def __init__(self, _redis, _db):
        self.__redis_conn = _redis
        self.__db_conn = _db

        self.__bind_ip = "0.0.0.0"
        self.__bind_port = 9998
        self.__temp_id = 1

        self.__room_name_list = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        self.__client_list = []

        self.__server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__server.bind((self.__bind_ip, self.__bind_port))

        self.__operation_thread = threading.Thread()
        self.is_running = False

    # 啟動
    def start(self):
        self.is_running = True
        self.__server.listen(5)
        self.__server.setblocking(False)
        self.__operation_thread = threading.Thread(target=self.__listen_operation)
        self.__operation_thread.start()

    # 停止
    def stop(self):
        self.is_running = False

    # 取得房間名稱
    def __get_room_name(self, index):
        _i_list = []
        _count = len(self.__room_name_list)
        _temp = index
        while True:
            _quo = _temp / _count
            _remain = _temp % _count
            _i_list.append(_remain)

            if _quo == 0:
                break
            else:
                _temp = _quo

        _name = ''
        for _i in _i_list:
            _name = self.__room_name_list[_i] + _name

        return _name

    # 取得房間列表
    def get_room_list(self):
        _response = SelectChatRoomResponse()
        for _cli in self.__client_list:
            _response.chat_room_list.append(_cli.get_room_info())

        return _response

    # 檢查重複登入
    def check_duplicate(self, _user_uid, _user_id):
        _request = S2SCheckDuplicate()
        _request.user_uid = _user_uid
        _request.user_id = _user_id

        for _cli in self.__client_list:
            _cli.send_check_duplicate(_request)

    # 監聽程序
    def __listen_operation(self):
        print "Wait Chat Room on %s:%d" % (self.__bind_ip, self.__bind_port)

        while self.is_running:
            # noinspection PyBroadException
            try:
                # noinspection PyBroadException
                try:
                    # 監聽來自其他的連線
                    new_connection, _address = self.__server.accept()
                    print 'Chat Room Connected by ', _address
                    try:
                        _new_s2s_connection = ChatRoomS2SCon(new_connection, self.__db_conn, self.__redis_conn)
                        _new_s2s_connection.client_id = self.__temp_id
                        _new_s2s_connection.room_name = self.__get_room_name(self.__temp_id - 1)
                        _new_s2s_connection.room_port = 8000 + self.__temp_id

                        self.__client_list.append(_new_s2s_connection)
                        self.__temp_id += 1
                    except Exception as e:
                        print e
                except:
                    pass

                remove_list = []
                for i in range(len(self.__client_list)):
                    _cli = self.__client_list[i]
                    if not _cli.update():
                        _cli.disconnect()
                        remove_list.append(_cli)

                for r in remove_list:
                    self.__client_list.remove(r)
            except Exception as e:
                print e
                pass

        self.is_running = False
        print 'Chat Room Server Stop'
