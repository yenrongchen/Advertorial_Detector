import json
import os
import re

POST_DIR = "posts"
POST_FILE = "./raw_data/dcard_name_raw.json"
MAPPING_FILE = "./id_mapping_name.json"
FORUM = "travel"

os.makedirs(POST_DIR, exist_ok=True)  # 確保資料夾存在

def main():
    try:
        with open(POST_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error: {e}")
        return

    article_id = 1
    id_mapping = {}  # 追蹤 Dcard 文章的原始 id 與 article_id 的對應關係
    
    for post in data:
        forum = post.get("forumAlias")
        if forum is None:
            print(f"找到一篇缺少論壇別的文章，ID: {id}")
            continue
        elif forum != FORUM:
            print(f"找到一篇論壇錯誤的文章，ID: {id}, 論壇: {forum}")
            continue

        post_id = post.get("id")
        true_content = ""
        url_pattern = re.compile(r'^(https?://[^\s]+)(\s+https?://[^\s]+)*$')
        content_raw = post.get("content")

        if url_pattern.match(content_raw.strip()):
            meta = post.get("meta", {})
            if "annotation" in meta and meta["annotation"].strip():
                true_content = meta["annotation"].strip()
            else:
                print(f"找到內文只有網址的文章，ID: {post_id}")
                continue
        else:
            true_content = content_raw

        with open(f"{POST_DIR}/{article_id}.txt", "w", encoding="utf-8") as f:
            f.write(f"標題：{post.get('title')}\n\n")
            f.write(true_content)

        id_mapping[post_id] = article_id
        article_id += 1
    
    # 另外存一份 ID 對照表
    with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
        json.dump(id_mapping, f, ensure_ascii=False, indent=2)

    print(f"已將 {article_id - 1} 篇文章儲存成文字檔")


if __name__ == "__main__":
    main()