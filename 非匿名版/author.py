import json
import time
import random
from playwright.sync_api import sync_playwright

POST_FILE = "dcard_name_raw.json"
OUTPUT_FILE = "author_posts.json"
PROCESSED_UIDS_FILE = "processed_uids.txt"
SAVE_EVERY = 50

def load_existing_data():
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def load_processed_uids():
    try:
        with open(PROCESSED_UIDS_FILE, "r") as f:
            return set(f.read().splitlines())
    except FileNotFoundError:
        return set()

def save_all(data, processed_uids):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    with open(PROCESSED_UIDS_FILE, "w") as f:
        f.write("\n".join(processed_uids) + "\n")
    print(f"已儲存 {len(data)} 位作者的資料")

def fetch_user_posts_page(page, uid, page_key="", max_retries=10):
    url = f"https://www.dcard.tw/service/api/v2/personae/{uid}/posts?nsfw=true&lang=zh-TW"
    if page_key:
        url += f"&pageKey={page_key}"

    for retry in range(max_retries):
        try:
            result = page.evaluate(f"""
                async () => {{
                    const res = await fetch("{url}", {{
                        headers: {{
                            "accept": "*/*",
                            "sec-fetch-site": "same-origin",
                            "sec-fetch-mode": "cors",
                        }},
                        credentials: "include"
                    }});
                    if (!res.ok) return {{ error: res.status }};
                    return await res.json();
                }}
            """)

            if isinstance(result, dict) and "error" in result:
                if result["error"] == 429:
                    wait_time = 30 + (retry * 10)
                    print(f"  遇到 429，等 {wait_time} 秒後重試第 {retry + 1} 次...")
                    time.sleep(wait_time)
                    continue
                elif result["error"] == 401:
                    print("  遇到 401，重新整理頁面...")
                    page.reload()
                    time.sleep(5)
                    continue
                else:
                    return result  # 404 或其他錯誤直接回傳

            return result

        except Exception as e:
            print(f"  Playwright 執行錯誤: {e}，等 5 秒後重試...")
            time.sleep(5)
            continue

    return {"error": "MAX_RETRIES_EXCEEDED"}

def select_post_info(post):
    cleaned = {}
    cleaned["id"] = post["id"]
    cleaned["title"] = post["title"]
    cleaned["forumId"] = post["forumId"]
    cleaned["forumName"] = post["forumName"]
    cleaned["forumAlias"] = post["forumAlias"]
    cleaned["likeCount"] = post["likeCount"]
    cleaned["collectionCount"] = post["collectionCount"]
    cleaned["shareCount"] = post["shareCount"]
    cleaned["personaNickname"] = post["personaNickname"]
    cleaned["personaUid"] = post["personaUid"]
    return cleaned

def fetch_all_user_posts(page, uid):
    all_posts = []
    current_key = ""

    while True:
        result = fetch_user_posts_page(page, uid, page_key=current_key)

        if isinstance(result, dict) and "error" in result:
            print(f"  UID {uid} 發生錯誤: {result}")
            break

        widgets = result.get("widgets", [])
        if not widgets:
            break

        for widget in widgets:
            items = widget.get("forumList", {}).get("items", [])
            for item in items:
                if "post" in item:
                    all_posts.append(select_post_info(item["post"]))

        next_key = result.get("nextKey")
        if not next_key:
            break

        current_key = next_key
        time.sleep(random.uniform(1.0, 2.0))

    return all_posts

def main():
    all_data = load_existing_data()
    processed_uids = load_processed_uids()

    try:
        with open(POST_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"找不到檔案 {POST_FILE}，請確認。")
        return

    # 從文章列表提取不重複的 UID，並記錄每個 UID 對應的文章 ID
    uid_to_post_ids = {}
    for post in data:
        uid = post.get("author", {}).get("subtitle")
        post_id = str(post.get("id", ""))
        if uid and post_id != "None":
            uid_to_post_ids.setdefault(uid, []).append(post_id)

    print(f"共發現 {len(uid_to_post_ids)} 位不重複作者")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = context.pages[0]
        page.goto("https://www.dcard.tw/f/travel", wait_until="domcontentloaded")
        page.wait_for_timeout(4000)
        print("已成功接管瀏覽器，開始爬取作者發文資料...")

        try:
            for i, (uid, post_ids) in enumerate(uid_to_post_ids.items()):
                if uid in processed_uids:
                    print(f"已爬過 UID {uid}，跳過")
                    continue

                print(f"[{i+1}/{len(uid_to_post_ids)}] 爬取 {uid}...")
                posts = fetch_all_user_posts(page, uid)
                print(f"  ✓ {uid} 共發了 {len(posts)} 篇文章")

                all_data.append({
                    "uid": uid,
                    "post_ids": post_ids,
                    "total_post_count": len(posts),
                    "posts": posts
                })

                processed_uids.add(uid)

                if len(processed_uids) % SAVE_EVERY == 0:
                    save_all(all_data, processed_uids)

                time.sleep(random.uniform(1.0, 3.0))

        except KeyboardInterrupt:
            print("\n收到手動中斷指令")
        finally:
            save_all(all_data, processed_uids)

    print(f"\n完成，共爬取 {len(all_data)} 位作者的資料")

if __name__ == "__main__":
    main()