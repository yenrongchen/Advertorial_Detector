import json
import csv

POST_INFO_FILE = "./outputs/post_info.json"
AUTHORS_INFO_FILE = "./outputs/authors_info.json"
COMMENTS_INFO_FILE = "./outputs/comments_info.json"
OUTPUT_CSV_FILE = "./outputs/dcard_name.csv"
OUTPUT_FEAT_FILE = "./outputs/data.csv"

def main():
    # 讀取三個 JSON 檔案
    with open(POST_INFO_FILE, "r", encoding="utf-8") as f:
        post_data = json.load(f)

    with open(AUTHORS_INFO_FILE, "r", encoding="utf-8") as f:
        authors_data = json.load(f)

    with open(COMMENTS_INFO_FILE, "r", encoding="utf-8") as f:
        comments_data = json.load(f)

    # 將 comments_info 轉為以 id (字串) 為 key 的 dict，方便查詢
    comments_dict = {}
    for comment in comments_data:
        comments_dict[str(comment["id"])] = comment

    # 定義要從 post_info 中排除的欄位（非特徵欄位）
    post_exclude_fields = {
        "articleId", "title", "content", "authorName", "authorSubtitle", "forumName", "forumAlias", "createdAt"
    }

    # 定義要從 comments_info 中排除的欄位（id 已作為合併 key）
    comment_exclude_fields = {"id"}

    # 取得欄位名稱
    # post 欄位：保留 id 和 articleId 以及其他特徵欄位
    sample_post = post_data[0]
    post_fields = [k for k in sample_post.keys() if k not in post_exclude_fields]

    # author 欄位
    sample_author_key = next(iter(authors_data))
    author_fields = list(authors_data[sample_author_key].keys())
    author_csv_fields = author_fields

    # comment 欄位
    sample_comment = comments_data[0]
    comment_fields = [k for k in sample_comment.keys() if k not in comment_exclude_fields]

    # 組合所有 CSV 欄位
    csv_fields = post_fields + author_csv_fields + comment_fields

    # 逐筆合併資料
    rows = []
    for post in post_data:
        row = {}

        # 加入 post 特徵欄位
        for field in post_fields:
            row[field] = post.get(field)

        # 透過 authorSubtitle 對應 uid，加入 author 行為特徵
        uid = post.get("authorSubtitle")
        author_info = authors_data.get(uid, {})
        for field in author_fields:
            row[field] = author_info.get(field)

        # 透過 id 對應貼文 id，加入 comment 特徵
        post_id = str(post.get("id"))
        comment_info = comments_dict.get(post_id, {})
        for field in comment_fields:
            row[field] = comment_info.get(field)

        rows.append(row)

    # 寫入 CSV
    with open(OUTPUT_FEAT_FILE, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields)
        writer.writeheader()
        writer.writerows(rows)

    print(f"已成功產出特徵 CSV 檔案：{OUTPUT_FEAT_FILE}")
    print(f"共 {len(rows)} 筆資料，{len(csv_fields)} 個欄位")

    # 寫入 dcard_name.csv (儲存文章基本資訊)
    name_fields = ["id", "articleId", "title", "content", "createdAt"]
    with open(OUTPUT_CSV_FILE, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=name_fields)
        writer.writeheader()
        for post in post_data:
            writer.writerow({field: post.get(field) for field in name_fields})

    print(f"已成功產出文章資訊 CSV 檔案：{OUTPUT_CSV_FILE}")
    print(f"共 {len(post_data)} 筆資料，{len(name_fields)} 個欄位")


if __name__ == "__main__":
    main()
