# ChatRoomTest

## 目的

- 熟悉Python、MongoDB、Redis操作
- 練習使用Socket建立連線
- 練習架構規劃以及串聯各節點功能，嘗試讓系統正常運行

## 架構規劃

![](https://i.imgur.com/VuQaNrO.jpg)

- Lobby Server：大廳伺服器，負責處理登入/註冊/配發Token/聊天伺服器管理
- Chat Server：聊天伺服器，專門處理Client間進行聊天等訊息傳送，以及訊息存取等動作
- MongoDB：後台資料庫，存取用戶、聊天內容
- Redis：快存資料庫，存取用戶Token，以及各項資料流水號紀錄

## 功能規劃

1. 使用者登入/註冊功能
2. 聊天室選擇
3. 重複登入剔除
4. 訊息傳送
5. Lobby Server 和 ChatRoom Server 保持溝通
6. 聊天室加入/離開通知
7. 訊息保留10分鐘自動移除
8. 離線獎勵
9. 閒置3分鐘剔除
10. 登入天數累計

## 資料定義

### 用戶資料 (User)

| 欄位         | 型態   | 說明       |
|:------------ |:------ |:---------- |
| id           | int    | 用戶流水號 |
| account      | string | 帳號       |
| password     | string | 密碼       |
| display_name | string | 顯示名稱   |
| gender       | string | 性別       |
| age          | int    | 年齡       |
| location     | string | 區域分布   |
| score        | int    | 積分       |
| total_login_days      | int  | 總登入天數        |
| cumulative_login_days | int  | 累積登入天數      |
| join_time             | Date | 註冊日期，UTC     |
| last_login_time       | Date | 最後登入時間，UTC |
| last_logout_time      | Date | 最後登出時間，UTC |

### 訊息資料 (Message)

| 欄位            | 型態   | 說明             |
|:--------------- |:------ |:---------------- |
| msg_id          | int    | 訊息流水號       |
| room_name       | string | 訊息所在房間     |
| msg_is_sys      | bool   | 是否為系統訊息   |
| msg_content     | string | 訊息內容         |
| msg_user_id     | int    | 訊息來源用戶編號 |
| msg_user_name   | string | 訊息來源用戶名稱 |
| msg_time        | Date   | 訊息發出時間     |
| msg_expire_time | Date   | 訊息到期時間     |
