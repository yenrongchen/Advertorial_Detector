import pandas as pd
import time
from playwright.sync_api import sync_playwright

AMOUNT = 3000

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
            time.sleep(30)
            continue
        elif detail.get("error") == 401:
            page.reload()
            time.sleep(5)
            continue
        elif detail.get("error") == 404:
            return {"error": 404}

        return detail
    
    return {"error": 429}

def main():
    data = pd.read_csv("dcard_name.csv", encoding="utf-8")
    data = data.sort_values("totalCommentCount", ascending=False)

    top = data[:AMOUNT]
    top_ids = top["id"].to_list()

    deleted = []

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = context.pages[0]

        for post_id in top_ids:
            res = fetch_post(page, post_id)
            if isinstance(res, dict) and res.get("error") == 404:
                deleted.append(str(post_id))

    with open("deleted.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(deleted))


if __name__ == "__main__":
    main()