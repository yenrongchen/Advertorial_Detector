import time
import json
import random
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse, parse_qs

FORUM = "travel"  # 要爬的看板名稱 (英文)
OUTPUT_FILE = "dcard_name_raw.json"  # 文章輸出檔案名稱
CRAWLED_IDS_FILE = "crawled_ids_name.txt"  # 記錄爬過的文章 ID
SAVE_EVERY = 50  # 每爬 50 篇就存檔一次
TARGET_AMOUNT = 5200  # 目標文章數量

def get_start_post_id(crawled_ids):
    if not crawled_ids:
        return None
    ids = sorted([int(i) for i in crawled_ids if i.isdigit()])
    if not ids:
        return None
    idx = int(len(ids) * 0.01)  # 第 1 百分位數的 ID 作為起點
    return ids[idx]

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
    print(f"已存 {len(posts)} 篇文章，{len(crawled_ids)} 個爬過的 ID")


def fetch_post(page, post_id, max_retries=5):
    for _ in range(max_retries):
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
            print("  429，等 30 秒...")
            time.sleep(30)
            continue

        return detail
    
    return {"error": 429}

def main():
    crawled_ids = load_crawled_ids()
    all_posts = load_existing_posts()
    start_id = get_start_post_id(crawled_ids)
    print(f"已存 {len(all_posts)} 篇，已爬過 {len(crawled_ids)} 個 ID")
    print(f"目標：{TARGET_AMOUNT} 篇\n")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = context.pages[0]
        print("已接管:", page.title())

        # 攔截 globalPaging 取得 listKey 和 pageKey
        captured = {}

        def handle_response(response):
            if "globalPaging/page" in response.url and "listKey" in response.url:
                if "list_key" not in captured:
                    params = parse_qs(urlparse(response.url).query)
                    captured["list_key"] = params.get("listKey", [None])[0]
                    captured["page_key"] = params.get("pageKey", [None])[0]
                    print("已攔到 keys")

        page.on("response", handle_response)

        # 載入旅遊版觸發 globalPaging 請求
        page.goto(f"https://www.dcard.tw/f/{FORUM}", wait_until="domcontentloaded")
        page.wait_for_timeout(4000)

        if "list_key" not in captured:
            print("沒攔到 keys，請確認頁面有正常載入")
            return

        list_key = captured["list_key"]
        if start_id:
            page_key = f"{list_key}_{start_id}"
            print(f"使用 {start_id} 當作起點")
        else: 
            page_key = captured["page_key"]

        new_since_save = 0

        try:
            while len(all_posts) < TARGET_AMOUNT:
                print(f"\n來到新的一頁，目前 {len(all_posts)}/{TARGET_AMOUNT} 篇")

                result = page.evaluate(f"""
                    async () => {{
                        const res = await fetch(
                            "/service/api/v2/globalPaging/page?enrich=true&platform=web&filterPolitical=false" +
                            "&listKey={list_key}&country=TW&lang=zh-TW&pageKey={page_key}&offset=0",
                            {{
                                headers: {{
                                    "accept": "*/*",
                                    "sec-fetch-site": "same-origin",
                                    "sec-fetch-mode": "cors",
                                }},
                                credentials: "include"
                            }}
                        );
                        if (!res.ok) return {{ "error": res.status }};
                        return await res.json();
                    }}
                """)

                if isinstance(result, dict) and result.get("error"):
                    if result["error"] == 429:
                        print("status 429，等 30 秒...")
                        time.sleep(30)
                        continue
                    elif result["error"] == 401:
                        print("status 401 session 過期，重新載入頁面...")
                        
                        # 重新載入頁面，重新攔截 keys
                        captured.clear()
                        page.goto(f"https://www.dcard.tw/f/{FORUM}", wait_until="domcontentloaded")
                        page.wait_for_timeout(4000)
                        
                        if "list_key" not in captured:
                            print("重新攔截失敗")
                            break
                        
                        list_key = captured["list_key"]
                        start_id = get_start_post_id(crawled_ids)
                        if start_id:
                            page_key = f"{list_key}_{start_id}"
                            print(f"使用 {start_id} 當作起點")
                        else: 
                            page_key = captured["page_key"]
                        print(f"重新取得 keys，繼續爬...")
                        continue
                    else:
                        print(f"status {result['error']}")
                        break

                for widget in result.get("widgets", []):
                    if len(all_posts) >= TARGET_AMOUNT:
                        break

                    if "forumList" in widget:
                        for item in widget["forumList"].get("items", []):
                            if "post" not in item:
                                continue

                            post_id = str(item["post"]["id"])
                            if post_id in crawled_ids:
                                print(f"  已爬過 {post_id}，跳過")
                                continue

                            time.sleep(random.uniform(1, 3))

                            detail = fetch_post(page, post_id)
                            if detail.get("error"):
                                continue

                            crawled_ids.add(post_id)

                            # 檢查 forum
                            if detail.get("forumAlias") != FORUM:
                                print(f"  跳過論壇錯誤的文章: {post_id}")
                                continue
                            
                            # 跳過匿名發布的文章
                            if not detail.get("withNickname", False):
                                print(f"  跳過匿名發布的文章: {post_id}")
                                continue

                            if detail.get("author", {}).get("type", "") != "IDENTITY_NICKNAME":
                                print(f"  跳過非實名發布的文章: {post_id}")
                                continue

                            # 跳過互動性過低的文章 (選用)
                            # if detail.get("totalCommentCount", 0) < 10 and detail.get("likeCount", 0) < 20:
                            #     print(f"  跳過互動性過低的文章: {post_id}")
                            #     continue

                            all_posts.append(detail)
                            new_since_save += 1
                            print(f"  [{len(all_posts)}] {detail.get('title', '')}")

                            if new_since_save >= SAVE_EVERY:
                                save_all(all_posts, crawled_ids)
                                new_since_save = 0

                            if len(all_posts) >= TARGET_AMOUNT:
                                break

                # 用 nextKey 翻頁
                next_key = result.get("nextKey")

                if not next_key:
                    print("沒有下一頁，結束")
                    break

                page_key = next_key
                time.sleep(random.uniform(3, 4))

        except KeyboardInterrupt:
            print("\n手動中斷")
        finally:
            save_all(all_posts, crawled_ids)

    print(f"\n完成！共 {len(all_posts)} 篇，存到 {OUTPUT_FILE}")

if __name__ == "__main__":
    main()