import json
import os
import re
import csv
from datetime import datetime, timezone, timedelta

def clean_data(article_dir, input_file, output_file, mapping_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error: {e}")
        return

    cleaned_data = []

    os.makedirs(article_dir, exist_ok=True)  # 確保資料夾存在
    article_id = 1
    id_mapping = {}  # 追蹤 Dcard 文章的原始 id 與 article_id 的對應關係

    print(f"處理 {len(data)} 篇文章中...")

    for post in data:
        id = post.get("id")
        forum = post.get("forumAlias")
        if forum is None:
            print(f"找到一篇缺少論壇別的文章，ID: {id}")
            continue
        elif forum != "travel":
            print(f"找到一篇論壇錯誤的文章，ID: {id}, 論壇: {forum}")
            continue

        # 萃取需要的欄位
        item = {
            "id": str(id),
            "articleId": str(article_id),
            "title": post.get("title"),
            "edited": int(post.get("edited", False)),
            "commentCount": int(post.get("commentCount")),
            "totalCommentCount": int(post.get("totalCommentCount")),
            "likeCount": int(post.get("likeCount")),
            "collectionCount": int(post.get("collectionCount")),
            "shareCount": int(post.get("shareCount")),
            "forumName": post.get("forumName"),
            "forumAlias": forum,
            "linksCount": len(post.get("links", [])),
            "authorUseNickname": int(post.get("withNickname")),
        }

        # 處理內文
        true_content = ""
        url_pattern = re.compile(r'^https?://[^\s]+$')
        content_raw = post.get("content")
        if url_pattern.match(content_raw.strip()):
            meta = post.get("meta", {})
            if "annotation" in meta:
                true_content = meta["annotation"].strip()
                item["content"] = true_content
            else:
                print(f"找到內文只有網址的文章，ID: {id}")
                continue
        else:
            true_content = content_raw
            item["content"] = true_content

        # 處理 createdAt 時間格式，轉換為台灣時間
        created_at = str(post.get("createdAt"))
        if created_at:
            utc_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            tz_taiwan = timezone(timedelta(hours=8))
            local_dt = utc_dt.astimezone(tz_taiwan)
            item["createdAt"] = local_dt.strftime("%Y-%m-%d %H:%M:%S")

        # 計算 image 和 video 數量
        media_meta = post.get("mediaMeta")
        unique_images = set()
        unique_videos = set()
        for m in media_meta:
            m_id = m.get("id")
            m_type = m.get("type", "")
            if m_id:
                if "image" in m_type:
                    unique_images.add(m_id)
                elif "video" in m_type:
                    unique_videos.add(m_id)
        
        item["withImages"] = 1 if len(unique_images) > 0 else 0
        item["withVideos"] = 1 if len(unique_videos) > 0 else 0
        item["imageCount"] = len(unique_images)
        item["videoCount"] = len(unique_videos)

        # 擷取作者資訊
        author = post.get("author", {})
        item["authorName"] = author.get("displayName")
        item["authorSubtitle"] = author.get("subtitle", "")
        
        item["authorHasCreatorBadge"] = int(post.get("creatorBadge", False))
        item["authorHasOfficialCreatorBadge"] = int(post.get("officialCreatorBadge", False))

        cleaned_data.append(item)

        with open(f"{article_dir}/{article_id}.txt", "w", encoding="utf-8") as f:
            f.write(f"標題：{post.get('title')}\n\n")
            f.write(true_content)

        id_mapping[id] = article_id
        article_id += 1

    # 寫入 CSV 檔案
    if cleaned_data:
        try:
            keys = cleaned_data[0].keys()
            with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
                dict_writer = csv.DictWriter(f, fieldnames=keys)
                dict_writer.writeheader()
                dict_writer.writerows(cleaned_data)
            
            # 另外存一份 ID 對照表
            with open(mapping_file, 'w', encoding='utf-8') as f:
                json.dump(id_mapping, f, ensure_ascii=False, indent=2)
            
            print(f"成功清理 {len(cleaned_data)} 篇文章，並存進 '{article_dir}/' 資料夾中。")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("沒有資料可以寫入。")

if __name__ == "__main__":
    clean_data(
        'posts', 
        'dcard_raw.json', 
        'dcard.csv', 
        'id_mapping.json'
    )