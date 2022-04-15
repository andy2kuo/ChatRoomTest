# -*- coding: utf-8 -*-
import json
import socket
import sys
import threading
import time
import uuid
from datetime import datetime

from Model.OperationCode import OperationCode
from Model.Login import LoginRequest, LoginResponse
from Model.Ping import Ping
from Model.Register import RegisterRequest, RegisterResponse
from Model.User import User
from Package.Packer import Packer

reload(sys)
sys.setdefaultencoding('utf-8')


# 大廳用戶連接器
class LobbyCliCon:
    def __init__(self, _client_id, _conn, _db, _redis):
        self.__user = User()
        self.is_connected = True
        self.client_id = _client_id
        self.__conn = _conn
        self.__conn.setblocking(0)
        self.__db = _db
        self.__redis = _redis
        self.__ping_time = time.clock()
        self.__packer = Packer()

        self.get_room_list = None
        self.check_duplicate = None

    # 封包處理
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

        return time.clock() - self.__ping_time <= 5 and self.is_connected

    # 重置Ping確認時間
    def __reset_ping_time(self):
        self.__ping_time = time.clock()

    # 處理回覆
    def get_response(self, _code, _data):
        self.__reset_ping_time()

        # Ping
        if _code == OperationCode.OP_PING:
            _response = Ping(i_data=json.loads(str(_data)))
            return True, _response.pack()
        # 登入請求
        elif _code == OperationCode.OP_LOGIN:
            _request = LoginRequest(i_data=json.loads(str(_data).encode('utf-8')))
            _get_user = self.__db.get_account(_request.account)

            _response = LoginResponse()
            _user_uid = str(uuid.uuid4())
            _response.user_uid = _user_uid
            _response.login_result = False
            if _get_user and _get_user.password == _request.password:
                _response.login_result = True
                _response.user = _get_user
                self.__user = _get_user
                # 比較最後登出時間，每隔10分鐘給一點會員積分
                _login_time = datetime.utcnow()
                _score = (_login_time - self.__user.last_logout_time).seconds / 600
                if _score > 0:
                    _response.user.score = self.__db.update_user_score(self.__user.id, _score)
                # 檢查登入天數需不需要更新
                _con_day = 0
                _total_day = 0
                _delta_time = _login_time.replace(hour=0, minute=0, second=0, microsecond=0) - \
                              _response.user.last_login_time.replace(hour=0, minute=0, second=0, microsecond=0)
                # 如果距離上次登入時間已跨日，總天數+1
                if _delta_time.days >= 1:
                    _total_day = 1
                    # 如果跨日且只間隔一天，連續天數+1
                    if _delta_time.days == 1:
                        _con_day = 1

                self.__db.update_last_login_info(self.__user.id, _login_time, _con_day, _total_day)
                # 發送檢查重複登入指令
                self.check_duplicate(_user_uid, self.__user.id)

            return True, _response.pack()
        # 註冊請求
        elif _code == OperationCode.OP_REGISTER:
            _request = RegisterRequest(json.loads(str(_data).encode('utf-8')))
            result, user = self.__db.add_account(_request)
            _response = RegisterResponse()
            _response.user = user

            if user:
                _response.register_result = True
                print user.display_name, 'register and login success'
            else:
                _response.register_result = False
                print 'register and login fail'

            return True, _response.pack()
        # 取得聊天室列表
        elif _code == OperationCode.OP_GET_CHAT_ROOM_LIST:
            _response = self.get_room_list()
            return True, _response.pack()
        else:
            return False, None

    # 將客戶端斷線
    def disconnect(self):
        if not self.__user:
            print 'disconnect'
        else:
            print self.__user.display_name, 'disconnect'
            self.__db.update_last_logout_time(self.__user.id)

        if self.is_connected:
            # noinspection PyBroadException
            try:
                self.__conn.shutdown(socket.SHUT_RDWR)
                self.__conn.close()
            except:
                pass

        self.is_connected = False


# 大廳用戶伺服器監聽器
class LobbyListener:
    def __init__(self, _redis, _db):
        self.__redis_conn = _redis
        self.__db_conn = _db

        self.__bind_ip = "0.0.0.0"
        self.__bind_port = 9999
        self.__temp_id = 1

        # 儲存所有連接的Client列表
        self.__client_list = []
        # 取得房間列表的Callback
        self.get_room_list = None
        # 確認是否有重複使用者的Callback
        self.check_duplicate = None

        # 產生Socket Server實例
        self.__server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__server.bind((self.__bind_ip, self.__bind_port))

        # 確認連線的執行緒
        self.__operation_thread = threading.Thread()
        self.is_running = False

    # 啟動
    def start(self):
        self.is_running = True
        self.__server.listen(5)
        # 設定 non-blocking
        self.__server.setblocking(False)
        self.__operation_thread = threading.Thread(target=self.__listen_operation)
        self.__operation_thread.start()

    # 停止
    def stop(self):
        self.is_running = False

    # 監聽程序
    def __listen_operation(self):
        print "Lobby Server Listening on %s:%d" % (self.__bind_ip, self.__bind_port)

        while self.is_running:
            # noinspection PyBroadException
            try:
                new_connection, _address = self.__server.accept()
                print 'Lobby Server Connected by ', _address
                try:
                    # 有新的連線進來
                    _cli = LobbyCliCon(self.__temp_id, new_connection, self.__db_conn, self.__redis_conn)
                    _cli.get_room_list = self.get_room_list
                    _cli.check_duplicate = self.check_duplicate
                    self.__client_list.append(_cli)
                    self.__temp_id += 1
                except Exception as e:
                    print e
            except:
                pass

            remove_list = []
            for i in range(len(self.__client_list)):
                _cli = self.__client_list[i]
                if not _cli.update():
                    print _cli.client_id, 'fail'
                    _cli.disconnect()
                    remove_list.append(_cli)

            for r in remove_list:
                self.__client_list.remove(r)

        self.is_running = False
        print 'Lobby Server Stop'
