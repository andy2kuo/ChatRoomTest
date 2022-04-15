# -*- coding: utf-8 -*-

import Tkinter as tk
import ttk
import datetime

from Connector import Connector
import sys
import time

from Model.ChatRoom import ChatRoomInfo
from Model.Login import LoginRequest
from Model.SendMessageRequest import SendMessageRequest, SyncMessage
from Model.Register import RegisterRequest
from Model.User import User

reload(sys)
sys.setdefaultencoding("utf-8")


# 聊天室 GUI
class ChatRoom(tk.Tk):
    # 聊天室 GUI 初始化
    def __init__(self, *args, **kwargs):

        tk.Tk.__init__(self, *args, **kwargs)
        self.title('聊天室實作')
        self.resizable(False, False)
        # 創建 tkinter 框架
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # 將各個頁面的框架生成後暫存
        self.frames = {}
        for F in (LoginPage, RegisterPage, ChatPage):
            frame = F(container, self)

            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(LoginPage)

    # 切換框架
    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()
        frame.on_raise()


# 登入頁面
class LoginPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        # 登入頁標題文字框
        login_title_label = ttk.Label(self, text='登入頁', font=large_font)
        login_title_label.grid(row=0, column=0, rowspan=2, columnspan=2, sticky='w', padx=5, pady=5)

        # 帳號文字框
        account_label = ttk.Label(self, text='帳號：')
        account_label.grid(row=2, sticky='w', padx=5, pady=5)

        # 帳號輸入框
        self.account_entry = ttk.Entry(self)
        self.account_entry.grid(row=2, column=1, sticky='w', padx=5, pady=5)

        # 密碼文字框
        password_label = ttk.Label(self, text='密碼：')
        password_label.grid(row=3, column=0, sticky='w', padx=5, pady=5)

        # 密碼輸入框
        self.password_entry = ttk.Entry(self, show='*')
        self.password_entry.grid(row=3, column=1, sticky='w', padx=5, pady=5)

        # 宣告 房間列表陣列
        self.room_selection = ['no room']

        # 位置文字框
        room_label = ttk.Label(self, text='位置：')
        room_label.grid(row=4, column=0, sticky='w', padx=5, pady=5)

        # 房間選擇下拉列表
        self.room_combobox = ttk.Combobox(self, values=self.room_selection, state='readonly')
        self.room_combobox.current(0)
        self.room_combobox.grid(row=4, column=1, sticky='w', padx=5, pady=5)

        # 重新整理按鈕
        self.refresh_btn = ttk.Button(self, text='重整', command=lambda: self.get_chat_room_list())
        self.refresh_btn.grid(row=4, column=2, padx=4, pady=4)

        # 登入按鈕
        self.login_btn = ttk.Button(self, text='進入',
                                    command=lambda: self.click_login())
        self.login_btn.grid(row=5, column=0, padx=5, pady=5)

        # 登入狀態訊息
        self.login_msg = tk.StringVar('')
        # 登入狀態文字框
        self.login_msg_label = ttk.Label(self, text='', textvariable=self.login_msg)
        self.login_msg_label.grid(row=5, column=1, padx=5, pady=5)

        # 前往註冊頁面按鈕
        self.register_btn = ttk.Button(self, text='註冊',
                                       command=lambda: self.click_register())
        self.register_btn.grid(row=6, column=0, padx=5, pady=5)

        # 宣告 房間資料陣列
        self.__room_info_list = []

    # 當頁面開啟時
    def on_raise(self):
        self.controller.geometry('370x220')
        self.get_chat_room_list()

    # 發送取得聊天室列表請求
    def get_chat_room_list(self):
        connector.on_get_room_list = self.on_get_room_list
        connector.get_room_list()

    # 取得聊天室列表回應時
    def on_get_room_list(self, _response):
        self.room_selection = []
        self.__room_info_list = _response.chat_room_list
        if len(_response.chat_room_list) > 0:
            # 將房間資訊列表轉換為GUI用的字串列表
            for _room in _response.chat_room_list:
                self.room_selection.append('%s (%s/%s)' % (_room.name, _room.now_user_count, _room.limit_user_count))
        else:
            self.room_selection = ['no room']

        # 重新建立房間列表選項GUI
        self.room_combobox.destroy()
        self.room_combobox = ttk.Combobox(self, values=self.room_selection, state='readonly')
        self.room_combobox.current(0)
        self.room_combobox.grid(row=4, column=1, sticky='w', padx=5, pady=5)
        self.room_combobox.update()

    # 在登入頁面點擊登入按鈕時
    def click_login(self):
        if len(self.__room_info_list) <= 0:
            self.login_msg.set("沒有房間選擇")
            self.login_msg_label.config(foreground='red')
            return

        # 登入狀態訊息清空
        self.login_msg.set("")

        # 取出帳號及密碼輸入內容
        account = self.account_entry.get()
        password = self.password_entry.get()

        # 如果目前為未連線狀態
        if not connector.is_connect():
            self.login_msg.set("連線失敗")
            self.login_msg_label.config(foreground='red')
            return

        # 設定登入回應接口
        connector.on_login_response = self.response_on_login

        _request = LoginRequest()
        _request.account = account
        _request.password = password

        # 發送登入請求
        result = connector.login(_request)
        if result:
            self.login_msg.set("等待回應")
            self.login_msg_label.config(foreground='blue')
        else:
            self.login_msg.set("登入時發生錯誤")
            self.login_msg_label.config(foreground='red')

    # 收到登入回應
    def response_on_login(self, response):
        if response.login_result:
            global user
            user = response.user

            global room
            room = self.__room_info_list[self.room_combobox.current()]

            connector.connect_to_chat(room)
            connector.register_to_chat_room(response.user_uid, user)

            self.controller.show_frame(ChatPage)
        else:
            self.login_msg.set('登入失敗')
            self.login_msg_label.config(foreground='red')

    # 在登入頁面點擊註冊按鈕時
    def click_register(self):
        self.controller.show_frame(RegisterPage)


# 註冊頁面
class RegisterPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        # 性別選項
        self.gender_selection = ['男', '女']
        # 會員地區選項
        self.location_selection = ['臺北市', '新北市', '桃園市', '臺中市', '臺南市', '高雄市', '宜蘭縣', '新竹縣',
                                   '苗栗縣', '彰化縣', '南投縣', '雲林縣', '嘉義縣', '屏東縣', '花蓮縣', '臺東縣',
                                   '澎湖縣', '基隆市', '新竹市', '嘉義市']

        # 註冊頁標題文字框
        register_title_label = ttk.Label(self, text='註冊', font=large_font)
        register_title_label.grid(row=0, column=0, rowspan=2, columnspan=2, sticky='w', padx=5, pady=5)

        # 帳號文字框
        account_label = ttk.Label(self, text='帳號：')
        account_label.grid(row=2, column=0, sticky='w', padx=5, pady=5)

        # 帳號輸入框
        self.account_entry = ttk.Entry(self)
        self.account_entry.grid(row=2, column=1, sticky='w', padx=5, pady=5)

        # 密碼文字框
        password_label = ttk.Label(self, text='密碼：')
        password_label.grid(row=3, column=0, sticky='w', padx=5, pady=5)

        # 密碼輸入框
        self.password_entry = ttk.Entry(self, show='*')
        self.password_entry.grid(row=3, column=1, sticky='w', padx=5, pady=5)

        # 名稱文字框
        display_name_label = ttk.Label(self, text='名稱：')
        display_name_label.grid(row=4, column=0, sticky='w', padx=5, pady=5)

        # 名稱輸入框
        self.display_name_entry = ttk.Entry(self)
        self.display_name_entry.grid(row=4, column=1, sticky='w', padx=5, pady=5)

        # 性別文字框
        gender_label = ttk.Label(self, text='性別：')
        gender_label.grid(row=5, column=0, sticky='w', padx=5, pady=5)

        # 性別選擇下拉選單
        self.gender_combobox = ttk.Combobox(self, values=self.gender_selection, state='readonly')
        self.gender_combobox.current(0)
        self.gender_combobox.grid(row=5, column=1, sticky='w', padx=5, pady=5)

        # 年齡文字框
        age_label = ttk.Label(self, text='年齡：')
        age_label.grid(row=6, column=0, sticky='w', padx=5, pady=5)

        # 年齡輸入框
        self.age_entry = ttk.Entry(self)
        self.age_entry.grid(row=6, column=1, sticky='w', padx=5, pady=5)

        # 位置文字框
        location_label = ttk.Label(self, text='位置：')
        location_label.grid(row=7, column=0, sticky='w', padx=5, pady=5)

        # 位置選擇下拉選單
        self.location_combobox = ttk.Combobox(self, values=self.location_selection, state='readonly')
        self.location_combobox.current(0)
        self.location_combobox.grid(row=7, column=1, sticky='w', padx=5, pady=5)

        # 註冊請求發送按鈕
        self.register_btn = ttk.Button(self, text='送出',
                                       command=lambda: self.click_register())
        self.register_btn.grid(row=8, padx=5, pady=5)

        # 註冊狀態文字框
        self.register_msg = tk.StringVar('')
        self.register_msg_label = ttk.Label(self, text='', textvariable=self.register_msg)
        self.register_msg_label.grid(row=8, column=1, padx=5, pady=5)

        # 返回登入頁面按鈕
        self.back_btn = ttk.Button(self, text='返回',
                                   command=lambda: self.click_back())
        self.back_btn.grid(row=9, padx=5, pady=5)

    # 當註冊頁被喚醒
    def on_raise(self):
        self.controller.geometry('300x350')

    # 點擊註冊按鈕事件
    def click_register(self):
        # 取出註冊輸入內容
        account = self.account_entry.get()
        password = self.password_entry.get()
        display_name = self.display_name_entry.get()
        gender = self.gender_combobox.get()
        location = self.location_combobox.get()
        # noinspection PyBroadException
        try:
            age = int(self.age_entry.get())
        except:
            self.register_msg.set("年齡錯誤")
            self.register_msg_label.config(foreground='red')
            return

        if not connector.is_connect():
            self.register_msg.set("連線失敗")
            self.register_msg_label.config(foreground='red')
            return

        # 設定註冊回應接口
        connector.on_register_response = self.response_on_register

        request = RegisterRequest()
        request.account = account
        request.password = password
        request.display_name = display_name
        request.gender = gender
        request.age = age
        request.location = location

        # 發送註冊請求
        result = connector.register(request)
        if result:
            self.register_msg.set('等待回應')
            self.register_msg_label.config(foreground='blue')
        else:
            self.register_msg.set('註冊時發生錯誤')
            self.register_msg_label.config(foreground='red')

    # 註冊回應事件
    def response_on_register(self, response):
        if response.register_result:
            global user
            user = response.user
            self.register_msg.set('註冊成功')
            self.register_msg_label.config(foreground='blue')
            time.sleep(1)
            self.controller.show_frame(LoginPage)
        else:
            self.register_msg.set('註冊失敗')
            self.register_msg_label.config(foreground='red')

    # 返回登入頁面事件
    def click_back(self):
        self.controller.show_frame(LoginPage)


# 聊天頁面
class ChatPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        global room
        self.controller.title(room.name)

        # 聊天室訊息區
        self.chat_area = tk.Text(self,
                                 width=20,
                                 height=2,
                                 bg="#17202A",
                                 fg="#EAECEE",
                                 font="Helvetica 14",
                                 padx=5,
                                 pady=5)

        self.chat_area.place(relheight=0.85,
                             relwidth=1,
                             rely=0,
                             relx=0,
                             anchor='nw')

        self.chat_area.config(cursor="arrow")

        # 聊天室滾動條，指定聊天室訊息區
        self.scrollbar = ttk.Scrollbar(self.chat_area)
        # 控制y軸方向
        self.scrollbar.config(command=self.chat_area.yview)

        self.columnconfigure(2)

        # 設定下方區域底圖範圍
        self.labelBottom = tk.Label(self,
                                    bg="#ABB2B9",
                                    height=80)

        self.labelBottom.place(relwidth=1,
                               relheight=0.15,
                               relx=1,
                               rely=1,
                               anchor='se')

        # 訊息輸入框
        self.entryMsg = tk.Entry(self.labelBottom,
                                 bg="#2C3E50",
                                 fg="#EAECEE",
                                 font="Helvetica 13")
        self.entryMsg.place(relwidth=0.90718,
                            relheight=0.998,
                            rely=0.001,
                            relx=0.001)
        self.entryMsg.focus()

        # 訊息發送按鈕
        self.buttonMsg = tk.Button(self.labelBottom,
                                   text="發送",
                                   font="Helvetica 10 bold",
                                   width=20,
                                   bg="#ABB2B9",
                                   command=lambda: self.click_send())
        self.buttonMsg.place(relx=0.999,
                             rely=0.001,
                             relheight=0.998,
                             relwidth=0.09282,
                             anchor='ne')

    # 當聊天室頁面被喚醒
    def on_raise(self):
        connector.on_sync_message = self.on_sync_messages

        _request = SyncMessage()
        connector.sync_message(_request)
        self.controller.geometry('600x800')

    # 點擊發送按鈕
    def click_send(self):
        global user
        msg = self.entryMsg.get()
        _request = SendMessageRequest()
        _request.user_id = user.id
        _request.user_name = user.display_name
        _request.message = msg
        result = connector.send_message(_request)
        if result:
            self.entryMsg.delete(0, tk.END)
        else:
            print 'send message fail'

    # 收到同步訊息回應時
    def on_sync_messages(self, sync_message):
        for index in range(len(sync_message.message_list) - 1, -1, -1):
            self.on_receive_message(sync_message.message_list[index])
        else:
            print 'set receive message'
            connector.on_receive_message = self.on_receive_message

    # 收到新訊息時
    def on_receive_message(self, receive_message):
        global user
        offset = time.timezone / 3600
        _delta = datetime.timedelta(hours=offset)
        msg_time = receive_message.message_time - _delta
        if not receive_message.is_system:
            if receive_message.user_id != user.id:
                self.set_message(receive_message.user_name, receive_message.message,
                                 msg_time)
            else:
                self.set_message_mine(receive_message.message, msg_time)
        else:
            self.set_message_system(receive_message.message, msg_time)

    # 在聊天室新增訊息 - 第三者
    def set_message(self, name, msg, msg_time):
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END,
                              "%s: %s" % (name, msg) + "\n")
        self.chat_area.insert(tk.END,
                              "%s" % msg_time + "\n\n")

        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.see(tk.END)

    # 在聊天室新增訊息 - 自己
    def set_message_mine(self, msg, msg_time):
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END,
                              "我: %s" % msg + "\n")
        self.chat_area.insert(tk.END,
                              "%s" % msg_time + "\n\n")

        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.see(tk.END)

    # 在聊天室新增訊息 - 系統
    def set_message_system(self, msg, msg_time):
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END,
                              "<%s>" % msg + "\n")
        self.chat_area.insert(tk.END,
                              "%s" % msg_time + "\n\n")

        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.see(tk.END)


if __name__ == '__main__':
    connector = Connector()
    large_font = ("Verdana", 20)
    user = User()
    room = ChatRoomInfo()

    connector.connect('localhost', 9999)

    chat_room = ChatRoom()

    # 連線和GUI刷新都採用 non-blocking 的方式
    while True:
        try:
            # 接收來自Server的封包
            connector.update()
        except Exception as e:
            print 'connect', e
            break

        try:
            # 更新GUI畫面
            chat_room.update()
        except Exception as e:
            if connector.is_connect():
                connector.disconnect(False)
            print 'gui', e
            break

        # 連線失敗，自動關閉
        if connector.is_fail:
            print 'Connect fail. Auto destroy'
            break
        # 被Server剔除
        elif connector.is_kick_out:
            print 'Kick out by server. Auto destroy'
            break

    # 如果Server正在連線狀態，要先向Server發送斷線通知
    if connector.is_connect():
        connector.disconnect(False)
