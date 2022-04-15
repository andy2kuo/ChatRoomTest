# -*- coding: utf-8 -*-
import json
import threading
import socket
import time
from datetime import datetime

from Model.ChatRoom import JoinChatRoom
from Model.KickOut import KickOut
from Model.OperationCode import OperationCode
from Model.Ping import Ping
from Model.SendMessageRequest import SendMessageRequest, ReceiveMessage, SyncMessage
from Model.User import User
from Package.Packer import Packer


class UserCon:
    def __init__(self, _client_id, _conn, _db, _redis):
        self.__user = User()
        self.__user_uid = ''
        self.is_connected = True
        self.__is_duplicate = False
        self.client_id = _client_id
        self.__conn = _conn
        self.__conn.setblocking(0)
        self.__db = _db
        self.__redis = _redis
        self.__ping_time = time.clock()
        self.__packer = Packer()
        self.__idle_time = time.clock()

        self.room_name = ''

        self.on_client_connect = None
        self.on_client_disconnect = None
        self.on_client_kick_out = None

        self.on_client_send_message = None

        self.get_room_list = None

    # 更新Client處理
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
            if _package_data:
                _is_send, _send_package = self.get_response(_code, _package_data)
                if _is_send:
                    self.__conn.send(_send_package)

        return time.clock() - self.__ping_time <= 3 and self.is_connected

    # 重置Ping確認時間
    def __reset_ping_time(self):
        self.__ping_time = time.clock()

    # 是否閒置時間過長
    def is_idle_over(self):
        return time.clock() - self.__idle_time >= 180

    # 標記為重複登入
    def check_is_duplicate(self, _user_uid, _user_id):
        if self.__user_uid != '':
            if self.__user.id == int(_user_id) and self.__user_uid != _user_uid:
                self.__is_duplicate = True

    # 是否為重複登入
    def is_duplicate(self):
        return self.__is_duplicate

    # 處理回覆
    def get_response(self, _code, _data):
        self.__reset_ping_time()

        # Ping
        if _code == OperationCode.OP_PING:
            _response = Ping(i_data=json.loads(str(_data)))
            return True, _response.pack()
        # 發送訊息
        elif _code == OperationCode.OP_SEND_MESSAGE:
            self.__idle_time = time.clock()

            _request = SendMessageRequest(i_data=json.loads(str(_data)))
            _response = ReceiveMessage()
            _response.id = self.__redis.get_next_msg_id(self.room_name)
            _response.user_id = _request.user_id
            _response.user_name = _request.user_name
            _response.is_system = False
            _response.message = _request.message
            self.__db.add_message(self.room_name, _response)

            if self.on_client_send_message:
                self.on_client_send_message(_response)

            return False, None
        # 加入房間
        elif _code == OperationCode.OP_JOIN_ROOM:
            _request = JoinChatRoom(i_data=json.loads(str(_data)))
            self.__user = _request.user
            self.__user_uid = _request.user_uid
            if self.on_client_connect:
                self.on_client_connect(self.__user_uid, self.__user)
            return True, _request.pack()
        # 同步訊息請求
        elif _code == OperationCode.OP_SYNC_MESSAGE:
            _response = SyncMessage(i_data=json.loads(str(_data)))
            _msg_list = self.__db.get_room_messages(self.room_name)
            _response.message_list = _msg_list
            return True, _response.pack()
        else:
            return False, None

    # 發送訊息
    def send_message(self, _response):
        self.__conn.send(_response.pack())

    # 將客戶端斷線
    def disconnect(self):
        if not self.__user:
            print 'disconnect'
        else:
            if self.on_client_disconnect:
                self.on_client_disconnect(self.__user)
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

    # 剔除房間
    def kick_out(self):
        if not self.__user:
            print 'kick out'
        else:
            if self.on_client_kick_out:
                self.on_client_kick_out(self.__user)
            print self.__user.display_name, 'kick out'
            self.__db.update_last_logout_time(self.__user.id)

        self.__conn.send(KickOut().pack())

        if self.is_connected:
            # noinspection PyBroadException
            try:
                self.__conn.shutdown(socket.SHUT_RDWR)
                self.__conn.close()
            except:
                pass

        self.is_connected = False


class ChatUserListener:
    def __init__(self, _redis, _db):
        self.__id = 0
        self.__name = ''
        self.__create_time = datetime.utcnow()

        self.__redis_conn = _redis
        self.__db_conn = _db

        self.__bind_ip = "0.0.0.0"
        self.__bind_port = 9999
        self.__temp_id = 1

        self.__client_list = []

        self.__server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.__operation_thread = threading.Thread()
        self.is_running = False

    # 啟動
    def __start(self):
        self.is_running = True
        self.__operation_thread = threading.Thread(target=self.__listen_operation)
        self.__operation_thread.start()

    # 停止
    def stop(self):
        self.is_running = False

    # 設定伺服器資料
    def set_server_info(self, _response):
        self.__id = _response.id
        self.__name = _response.name
        self.__bind_port = _response.port
        self.__create_time = _response.create_time

        print 'set room info', self.__id, self.__name, self.__bind_port, self.__create_time

        self.__start()

    # 取得伺服器資訊
    def get_server_info(self):
        return self.__name, len(self.__client_list)

    # 驗證是否重複
    def check_duplicate_user(self, _user_uid, _user_id):
        for _cli in self.__client_list:
            _cli.check_is_duplicate(_user_uid, _user_id)

    # 客戶端連線進入
    def on_client_connect(self, i_user_uid, i_user):
        print '%s %s 已加入' % (i_user.display_name, i_user_uid)
        self.send_system_message('%s(積分%s) 已加入' % (i_user.display_name, i_user.score))

    # 客戶端斷開連線
    def on_client_disconnect(self, i_user):
        self.send_system_message('%s 已離開' % i_user.display_name)

    # 客戶端斷開連線
    def on_client_kick_out(self, i_user):
        self.send_system_message('%s 已被剔除' % i_user.display_name)

    # 發送系統訊息
    def send_system_message(self, message):
        _response = ReceiveMessage()
        _response.id = self.__redis_conn.get_next_msg_id(self.__name)
        _response.message = message
        _response.is_system = True
        self.__db_conn.add_message(self.__name, _response)

        for _cli in self.__client_list:
            _cli.send_message(_response)

    # 發送訊息
    def send_message(self, _message_data):
        for _cli in self.__client_list:
            _cli.send_message(_message_data)

    # 監聽程序
    def __listen_operation(self):
        self.__server.setblocking(False)
        self.__server.bind((self.__bind_ip, self.__bind_port))
        self.__server.listen(5)
        print "Wait Chat User on %s:%d" % (self.__bind_ip, self.__bind_port)

        while self.is_running:
            # noinspection PyBroadException
            try:
                new_connection, _address = self.__server.accept()
                print 'Connected by ', _address
                try:
                    _new_conn = UserCon(self.__temp_id, new_connection, self.__db_conn, self.__redis_conn)
                    _new_conn.room_name = self.__name
                    _new_conn.on_client_connect = self.on_client_connect
                    _new_conn.on_client_disconnect = self.on_client_disconnect
                    _new_conn.on_client_kick_out = self.on_client_kick_out
                    _new_conn.on_client_send_message = self.send_message
                    self.__client_list.append(_new_conn)
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
                elif _cli.is_idle_over() or _cli.is_duplicate():
                    _cli.kick_out()
                    remove_list.append(_cli)

            for r in remove_list:
                self.__client_list.remove(r)

        self.is_running = False
        print 'Chat User Server Stop'
