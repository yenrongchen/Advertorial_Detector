## 文章特徵

### 社交互動資訊
* `edited`: 是否編輯過
* `commentCount`: 直接回覆數量
* `totalCommentCount`: 總回覆數量
* `likeCount`: 按讚數
* `collectionCount`: 收藏數
* `shareCount`: 分享數


### 文本資訊
* `wordCount`: 文章字數
* `lfFreq`: 換行符號密度
* `linksCount`: 外部連結數量
* `utmLinksCount`: UTM 連結數量
* `emojiCount`: Emoji 頻率
* 特定標點符號頻率
* 特定促購或商業意圖詞彙詞彙頻率 (ex. CTA 詞彙、折扣詞、推銷詞、推薦詞、營造急迫感詞彙)
* `withImages`: 是否包含圖片
* `withVideos`: 是否包含影片
* `imageCount`: 圖片數量
* `videoCount`: 影片數量
* `imageTextRatio`: 圖片文字比例 (每千字)
* `videoTextRatio`: 影片文字比例 (每千字)
* `mediaTextRatio`: 媒體文字比例 (每千字)
* 情緒特徵 => 可多種


### 作者資訊
* `authorUseNickname`: 發文者是否為匿名 (待定)
* `authorHasCreatorBadge`: 發文者是否有創作者勳章
* `authorHasOfficialCreatorBadge`: 發文者是否有官方創作者勳章
* `authorSuspicious`: 是不是可疑帳號 (isSuspiciousAccount)


### 留言特徵
* 作者回覆佔比
* 作者回覆內的連結佔比
* 作者回覆內的 UTM 連結佔比
* 平均子留言深度
* 首留言時間差
* 前 10 分鐘留言佔總留言比例
* 留言情緒？


### 作者資訊及行為特徵
* 歷史發文數
* 歷史發文頻率
* 近 30 天內的發文數占比
* 時間內大量發文程度
* 最大 24 小時內發文數
* 發文間隔變異數
* 上班時間發文比率
* 周末發文比率
* 旅遊版文章佔所有貼文的比例
* 跨看板活躍度 (Cross-board Entropy) (要正規化)
* 發文平均讚數
* 文章模板相似度


### 怎麼處理？
* `title`: 文章標題
* `content`: 文章內文
* `createdAt`: 發表時間
