## 檔案結構

```text
非匿名版/
├── author.py                  ← 爬取作者所有貼文程式
├── author_info.py             ← 整理作者行為特徵程式
├── author_posts.json          ← 作者所有貼文的原始資料
├── check_exist.py             ← 檢查貼文存在狀況程式
├── comment.py                 ← 爬取文章留言程式
├── comments_info.json         ← 文章留言資訊
├── crawl.py                   ← 爬蟲主程式 (針對非匿名文章)
├── crawled_ids_name.txt       ← 已爬取的文章 ID 紀錄
├── csv_info.py                ← 彙整文章所有資訊程式
├── dcard_name.csv             ← 文章資訊彙整 (模型輸入資料)
├── dcard_name_raw.json        ← 爬取的原始文章資料 (JSON 格式)
├── id_mapping_name.json       ← 文章原始 ID 與檔名 ID 的對照表
├── post_to_csv.py             ← 整理資料程式
├── processed_comment_ids.txt  ← 已處理留言的文章 ID 紀錄
├── processed_uids.txt         ← 已處理作者的 UID 紀錄
├── README.md                  ← 說明文件 (You are here)
├── posts/                     ← 存放文章文字檔的資料夾
    ├── 1.txt
    ├── 2.txt
    └── ... (更多 txt 檔案)
```

<br>

## CSV 欄位解釋

| 欄位名稱 | 說明 |
| :--- | :--- |
| `id` | Dcard 原始文章 ID |
| `articleId` | `posts/` 資料夾下的檔名 ID |
| `title` | 文章標題 |
| `edited` | 是否編輯過 |
| `commentCount` | 直接回覆數量 |
| `totalCommentCount` | 總回覆數量 (含樓中樓) |
| `likeCount` | 按讚數 |
| `collectionCount` | 收藏數 |
| `shareCount` | 分享數 |
| `forumName` | 看板名稱 |
| `forumAlias` | 看板英文代號 |
| `linksCount` | 文章內連結數量 |
| `authorUseNickname` | 發文者是否為匿名 |
| `content` | 文章內文 |
| `createdAt` | 發表時間 |
| `withImages` | 是否包含圖片 |
| `withVideos` | 是否包含影片 |
| `imageCount` | 圖片數量 |
| `videoCount` | 影片數量 |
| `authorName` | 發文者名稱 |
| `authorSubtitle` | 發文者校系或身分說明 |
| `authorHasCreatorBadge` | 發文者是否有創作者勳章 |
| `authorHasOfficialCreatorBadge` | 發文者是否有官方創作者勳章 |

#### 註：`edited`、`authorUseNickname`、`withImages`、`withVideos`、`authorHasCreatorBadge`、`authorHasOfficialCreatorBadge` 六個欄位原為布林值，CSV 檔中已被轉換為整數，1 代表 True，0 代表 False

<br>

## 查看原始貼文方式

1. posts 資料夾裡面所有文章的檔名都是一個整數 ID (以下稱為「文章檔名 ID」)
2. 前往 [id_mapping_name.json](id_mapping_name.json)，裡面紀錄的格式如下： 
   ```json
   {
      "文章原始ID": 文章檔名 ID,
   }
   ```
3. 用文章檔名找到文章原始 ID
4. 原始貼文的網址就會是 https://www.dcard.tw/f/travel/p/ 加上「文章原始 ID」

### 範例：
* 根據 id_mapping.json，1.txt 對應到的原始文章 ID 是 261406898
* 原始貼文的網址就會是 https://www.dcard.tw/f/travel/p/261406898

<br>

## 爬蟲執行步驟

1. 終端機輸入 
   ```bash
   "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\chrome-debug"
   ```
2. 在自動開啟的瀏覽器進入 Dcard，登入 (如果未登入)，再前往旅遊板 (或任意想爬的板)
3. 執行
   ```
   python crawl_name.py
   ```
