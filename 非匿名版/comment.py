import json
import time
import random
from playwright.sync_api import sync_playwright

POST_FILE = "./raw_data/dcard_name_raw.json"
OUTPUT_FILE = "./raw_data/comments.json"
PROCESSED_IDS_FILE = "./record/processed_comment_ids.txt"
SAVE_EVERY = 50

def load_existing_comments():
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def load_processed_ids():
    try:
        with open(PROCESSED_IDS_FILE, "r") as f:
            return set(f.read().splitlines())
    except FileNotFoundError:
        return set()

def save_all(comments, processed_ids):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)

    with open(PROCESSED_IDS_FILE, "w") as f:
        f.write("\n".join(processed_ids) + "\n")

    print(f"已儲存 {len(comments)} 篇文章的留言資訊")

def fetch_comments(page, post_id, comment_type, comment_id="", after="", max_retries=10):
    # 抓取留言，支援分頁 (after 參數)、動態重試機制與 Playwright 例外捕捉
    base_url = f"https://www.dcard.tw/service/api/v2/posts/{post_id}/comments"
    params = []
    
    if comment_type == "sub" and comment_id:
        params.append(f"parentId={comment_id}")
    if after:
        params.append(f"after={after}")
        
    fetch_url = f"{base_url}?{'&'.join(params)}" if params else base_url

    for retry in range(max_retries):
        try:
            comments = page.evaluate(f"""
                async () => {{
                    const res = await fetch("{fetch_url}", {{
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

            if isinstance(comments, dict):
                if comments.get("error") == 429:
                    # 動態拉長等待時間 (30s -> 40s -> 50s...)
                    wait_time = 30 + (retry * 10)
                    print(f"遇到 429 限制，等 {wait_time} 秒後重試第 {retry + 1} 次...")
                    time.sleep(wait_time)
                    continue
                elif comments.get("error") == 401:
                    print("遇到 401 授權錯誤，重新整理頁面...")
                    page.reload()
                    time.sleep(5)
                    continue
                elif comments.get("error") == 404:
                    return {"error": 404}

            return comments
            
        except Exception as e:
            print(f"Playwright 執行錯誤: {e}\n等待 5 秒後重試...")
            time.sleep(5)
            continue
            
    return {"error": "MAX_RETRIES_EXCEEDED"}

def main():
    all_comments = load_existing_comments()
    processed_ids = load_processed_ids()

    try:
        with open(POST_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"找不到檔案 {POST_FILE}，請確認。")
        return

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = context.pages[0]
        page.goto(f"https://www.dcard.tw/f/travel", wait_until="domcontentloaded")
        page.wait_for_timeout(4000)
        print("已成功接管瀏覽器，開始爬取留言...")
        
        try:
            for post in data:
                post_id = str(post.get("id"))
                if post_id == "None":
                    print("發現文章沒有 ID，跳過")
                    continue
                
                if post_id in processed_ids:
                    print(f"已爬過 ID {post_id}，跳過")
                    continue
                
                # 分頁變數
                all_dir_comments = []
                last_dir_id = ""
                has_error = False

                # 爬取主留言 (加入分頁 while 迴圈)
                while True:
                    dir_comments = fetch_comments(page, post_id, "normal", after=last_dir_id)
                    
                    if isinstance(dir_comments, dict):
                        if dir_comments.get("error") == 404:
                            print(f"ID {post_id} 文章已經被刪除")
                        else:
                            print(f"ID {post_id} 文章抓取發生錯誤: {dir_comments}")
                        has_error = True
                        break

                    if not isinstance(dir_comments, list):
                        print(f"ID {post_id} 返回非預期格式")
                        has_error = True
                        break
                        
                    if len(dir_comments) == 0:
                        break  # 主留言到底了

                    for com in dir_comments:
                        comment_id = com.get("id")
                        if not comment_id:
                            continue
                        
                        if com.get("content") is None:
                            continue

                        # 爬取子留言 (加入分頁 while 迴圈)
                        if com.get("subCommentCount", 0) > 0:
                            all_sub_comments = []
                            last_sub_id = ""
                            
                            while True:
                                sub_comments = fetch_comments(page, post_id, "sub", comment_id, after=last_sub_id)

                                if isinstance(sub_comments, dict) and sub_comments.get("error"):
                                    print(f"留言 ID {comment_id} 的子留言錯誤: {sub_comments}")
                                    break
                                    
                                if not isinstance(sub_comments, list) or len(sub_comments) == 0:
                                    break  # 子留言到底了

                                all_sub_comments.extend(sub_comments)
                                
                                # 子留言翻頁判斷
                                if len(sub_comments) < 30: 
                                    break
                                else:
                                    last_sub_id = sub_comments[-1].get("floor")
                                    time.sleep(random.uniform(1.0, 3.0))

                            com["subComments"] = all_sub_comments
                            time.sleep(random.uniform(1.0, 2.0))

                    all_dir_comments.extend(dir_comments)
                    
                    # 主留言翻頁判斷
                    if len(dir_comments) < 30:
                        break
                    else:
                        last_dir_id = dir_comments[-1].get("floor")
                        time.sleep(random.uniform(1.5, 3.0))

                # 如果因為 404 或嚴重錯誤中斷，將這篇文章標記為完成 (避免無窮重試)，並跳過存檔
                if has_error and len(all_dir_comments) == 0:
                    processed_ids.add(post_id)
                    continue

                # 將該文章的所有留言統整存入
                all_comments.append({post_id: all_dir_comments})

                print(f"完成 ID {post_id} 的文章")
                processed_ids.add(post_id)

                if len(processed_ids) % SAVE_EVERY == 0:
                    save_all(all_comments, processed_ids)

                time.sleep(random.uniform(1.0, 3.0))

        except KeyboardInterrupt:
            print("\n收到手動中斷指令")

        finally:
            save_all(all_comments, processed_ids)

if __name__ == "__main__":
    main()