import json

POST_FILE = "./raw_data/dcard_name_raw.json"
AUTHOR_FILE = "./raw_data/author_posts.json"

def fetch_raw_post():
    with open(POST_FILE, "r", encoding="utf-8") as f:
        all_posts = json.load(f)

    post_map = {}

    for p in all_posts:
        info = {
            "id": p["id"],
            "title": p["title"],
            "forumId": p["forumId"],
            "forumName": p["forumName"],
            "forumAlias": p["forumAlias"],
            "likeCount": p["likeCount"],
            "collectionCount": p["collectionCount"],
            "shareCount": p["shareCount"],
            "createdAt": p["createdAt"],
            "personaNickname": p["personaNickname"],
            "personaUid": p["personaUid"],
        }
        post_map[str(p["id"])] = info

    return post_map

def main():
    post_map = fetch_raw_post()

    with open(AUTHOR_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    for entry in data:
        posts_ids = entry.get("post_ids", [])
        posts = entry.get("posts", [])
        count = entry.get("total_post_count", 0)

        cur_posts_ids = set()
        for p in posts:
            pid = p.get("id")
            if pid:
                cur_posts_ids.add(str(pid))

        for crawled_id in posts_ids:
            if crawled_id not in cur_posts_ids:
                posts.append(post_map[crawled_id])
                count += 1

        entry["total_post_count"] = count

    with open(AUTHOR_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()