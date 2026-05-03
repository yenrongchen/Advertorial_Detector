## 爬蟲執行步驟

1. 關閉所有 Chrome
2. 終端機輸入 
   ```bash
   "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\chrome-debug"
   ```
3. 在自動開啟的瀏覽器進入 Dcard，登入 (如果未登入)，再前往旅遊板 (或任意想爬的板)
4. 執行
   ```
   python crawl_name.py
   ```


## 查看原始貼文方式

1. posts 資料夾裡面所有文章的檔名都是一個整數 (副檔名是 txt)，記下那個整數
2. 前往 [id_mapping_name.json](id_mapping_name.json)，裡面紀錄的格式如下： 
   ```json
   {
      "原始文章ID": 文章檔名的整數,
   }
   ```
3. 用文章檔名找到原始文章 ID
4. 原始貼文的網址就會是 https://www.dcard.tw/f/travel/p/ 加上「原始文章 ID」

### 範例：
* 根據 id_mapping.json，1.txt 對應到的原始文章 ID 是 261406898
* 原始貼文的網址就會是 https://www.dcard.tw/f/travel/p/261406898
