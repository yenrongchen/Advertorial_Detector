import time
import json
import random
from playwright.sync_api import sync_playwright

FORUM = "travel"
CRAWLED_IDS_FILE = "crawled_ids.txt"
OUTPUT_FILE = "dcard_travel_raw.json"
SAVE_EVERY = 30
TARGET_POSTS = 2000

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
            print(f"  ⏳ 429，等 {wait} 秒後重試...")
            time.sleep(wait)
            continue
        return detail
    return {"error": 429}

def scroll_and_collect_ids(page, forum):
    """滾動頁面直到連續 3 次沒有新 ID，回傳這輪收集到的 ID"""
    page.goto(f"https://www.dcard.tw/f/{forum}", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    ids = set()
    last_count = 0
    no_change_count = 0

    while no_change_count < 3:
        new_ids = page.evaluate("""
            () => {
                const links = [...document.querySelectorAll('a[href*="/p/"]')];
                return links.map(a => a.href.match(/\\/p\\/(\\d+)/)?.[1]).filter(Boolean);
            }
        """)
        ids.update(new_ids)
        print(f"  📜 目前 {len(ids)} 個 ID")

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(random.randint(2000, 5000))

        if len(ids) == last_count:
            no_change_count += 1
            print(f"  ⚠️ 沒有新增（{no_change_count}/3）")
        else:
            no_change_count = 0
        last_count = len(ids)

    print(f"  ✅ 這輪滾動結束，共 {len(ids)} 個 ID")
    return ids

def crawl_ids(page, ids, all_posts, crawled_ids):
    """爬一批 ID，回傳新增篇數"""
    new_since_save = 0

    for i, post_id in enumerate(list(ids)):
        if len(all_posts) >= TARGET_POSTS:
            break

        if post_id in crawled_ids:
            print(f"[{i+1}/{len(ids)}] ⏭ 跳過 {post_id}")
            continue

        print(f"[{i+1}/{len(ids)}] 抓 {post_id}... (總進度 {len(all_posts)}/{TARGET_POSTS})")
        detail = fetch_post(page, post_id)

        crawled_ids.add(post_id)
        new_since_save += 1

        if detail.get("error"):
            print(f"  ❌ status {detail['error']}")
        else:
            all_posts.append(detail)
            print(f"  ✓ {detail.get('title')}")

        if new_since_save >= SAVE_EVERY:
            save_all(all_posts, crawled_ids)
            new_since_save = 0

        time.sleep(random.uniform(3, 5))

def main(forum=FORUM):
    crawled_ids = load_crawled_ids()
    all_posts = load_existing_posts()
    print(f"📂 已爬過 {len(crawled_ids)} 個 ID，已存 {len(all_posts)} 篇文章")
    print(f"🎯 目標：{TARGET_POSTS} 篇\n")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = context.pages[0]
        print("✅ 已接管:", page.title())

        round_num = 0
        try:
            while len(all_posts) < TARGET_POSTS:
                round_num += 1
                print(f"\n{'='*40}")
                print(f"🔄 第 {round_num} 輪，目前 {len(all_posts)}/{TARGET_POSTS} 篇")
                print(f"{'='*40}")

                # 滾動收集 ID
                ids = scroll_and_collect_ids(page, forum)

                # 過濾掉已爬過的
                new_ids = ids - crawled_ids
                print(f"\n🆕 這輪有 {len(new_ids)} 個新 ID 待爬")

                if not new_ids:
                    print("⚠️ 沒有新 ID，等 30 秒後重試...")
                    time.sleep(30)
                    continue

                # 爬這批 ID
                crawl_ids(page, new_ids, all_posts, crawled_ids)

                # 存檔（包含這輪還沒存的）
                save_all(all_posts, crawled_ids)

        except KeyboardInterrupt:
            print("\n⚠️ 手動中斷")
        finally:
            save_all(all_posts, crawled_ids)

    print(f"\n🎉 完成，共 {len(all_posts)} 篇，存到 {OUTPUT_FILE}")

if __name__ == "__main__":
    main()