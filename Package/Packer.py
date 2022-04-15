# -*- coding: utf-8 -*-
import struct


# 封包處理器
class Packer:
    def __init__(self):
        # 累積所有接收的封包資料
        self.__temp_data = ''
        # 標頭大小
        self.__header_size = 4 + 1
        # 紀錄當前接收中資料大小
        self.__now_package_data_length = -1
        # 已處理完畢的資料暫存區
        self.__now_package_tuple = (0, None)

    # 加入資料
    def add_data(self, _data):
        if len(_data) > 0:
            self.__temp_data += _data

    # 處理資料
    def process(self):
        # 如果目前有累積的封包
        while len(self.__temp_data) > 0:
            # 如果還未確定當前接收中資料的大小
            if self.__now_package_data_length < 0:
                # 累計的資料至少已經超過標頭大小，代表可以確認當前接收資料的總長度
                if len(self.__temp_data) >= self.__header_size:
                    self.__now_package_data_length, _now_package_code = \
                        self.__unpack_header(self.__temp_data[:self.__header_size])
                    self.__temp_data = self.__temp_data[self.__header_size:]
                    self.__now_package_tuple = (_now_package_code, None)
                    continue
                else:
                    return False
            else:
                # 如果累積的資料長度已經達到當前接收資料總長度甚至超過，代表可以先把該資料從累積的封包數據中擷取出來
                if 0 <= self.__now_package_data_length <= len(self.__temp_data):
                    # 將資料從累積封包中擷取出來並拆封
                    _package_data = self.__unpack_data(self.__now_package_data_length,
                                                       self.__temp_data[:self.__now_package_data_length])
                    # 將拆封後的資料暫存
                    self.__now_package_tuple = (self.__now_package_tuple[0], _package_data)

                    # 將累積封包中該資料的部分移除
                    self.__temp_data = self.__temp_data[self.__now_package_data_length:]
                    self.__now_package_data_length = -1

                    # 通知外部此次流程有一筆資料拆封
                    return True
                else:
                    return False

    # 取得封包
    def get_package(self):
        return self.__now_package_tuple[0], self.__now_package_tuple[1]

    # 封裝，輸入請求代碼及資料，回傳封裝後資料
    @staticmethod
    def pack(code, origin_data):
        data_length = len(origin_data)

        data = struct.pack('%ds' % data_length, origin_data)
        header = struct.pack('=IB', data_length, code)

        return header + data

    # 拆封標頭，回傳資料大小及請求代碼
    @staticmethod
    def __unpack_header(i_header):
        origin_header = struct.unpack('=IB', i_header)
        data_length = int(origin_header[0])
        code = int(origin_header[1])
        return data_length, code

    # 拆封資料，輸入資料大小及資料，回傳拆封資料結果
    @staticmethod
    def __unpack_data(i_length, i_data):
        origin_data = struct.unpack('%ds' % i_length, i_data)
        return origin_data[0]
