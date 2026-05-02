import time
import json
import random
from playwright.sync_api import sync_playwright

TARGET_FORUM = {"travel", "japan_travel", "korea_travel"}  ## 要爬的版的英文名稱 ##
CRAWLED_IDS_FILE = "crawled_ids.txt"
OUTPUT_FILE = "dcard_travel_raw.json"
SAVE_EVERY = 30  # 每 30 筆存一次

START_ID = 261391091
END_ID =   261300000

def load_crawled_ids():
    try:
        with open(CRAWLED_IDS_FILE, "r") as f:
            return set(f.read().splitlines())
    except FileNotFoundError:
        return set()

def load_existing_posts():
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_all(posts, crawled_ids):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    with open(CRAWLED_IDS_FILE, "w") as f:
        f.write("\n".join(crawled_ids) + "\n")
    print(f"💾 已存 {len(posts)} 篇文章，{len(crawled_ids)} 個爬過的 ID")


def fetch_post(page, post_id, max_retries=3):
    for attempt in range(max_retries):
        detail = page.evaluate(f"""
            async () => {{
                const res = await fetch("https://www.dcard.tw/service/api/v2/posts/{post_id}", {{
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

        if detail.get("error") == 429:
            wait = (attempt + 1) * 10
            print(f"  ⏳ 429，等 {wait} 秒...")
            time.sleep(wait)
            continue

        return detail
    
    return {"error": 429}

def main(target_forum):
    crawled_ids = load_crawled_ids()
    all_posts = load_existing_posts()
    new_since_save = 0
    print(f"📂 已爬過 {len(crawled_ids)} 個 ID，已存 {len(all_posts)} 篇 travel 文章")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = context.pages[0]
        print("✅ 已接管:", page.title())

        try:
            for post_id in range(START_ID, END_ID, -1):
                post_id_str = str(post_id)

                if post_id_str in crawled_ids:
                    print(f"⏭ 跳過 {post_id}")
                    continue

                print(f"🔍 檢查 {post_id}...")
                detail = fetch_post(page, post_id)

                crawled_ids.add(post_id_str)
                new_since_save += 1

                if detail.get("error"):
                    print(f"  ❌ status {detail['error']}")
                else:
                    forum = detail.get("forumAlias", "")
                    if forum in target_forum:
                        all_posts.append(detail)  # 存整個 detail
                        print(f"  ✓ [{len(all_posts)}] {detail.get('title')}")
                    else:
                        print(f"  ➡ Forum: {forum}，跳過")

                if new_since_save >= SAVE_EVERY:
                    save_all(all_posts, crawled_ids)
                    new_since_save = 0

                time.sleep(random.uniform(1, 3))

        except KeyboardInterrupt:
            print("\n⚠️ 手動中斷")

        finally:
            # 不管正常結束還是中斷，最後都存一次
            save_all(all_posts, crawled_ids)

    print(f"\n🎉 完成，共找到 {len(all_posts)} 篇 travel 文章")

if __name__ == "__main__":
    main(target_forum=TARGET_FORUM)