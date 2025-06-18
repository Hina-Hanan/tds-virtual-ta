import requests
import json
from dateutil.parser import parse
import time
from datetime import datetime

START = datetime.strptime('2025-01-01', "%Y-%m-%d").date()
END   = datetime.strptime('2025-04-14', "%Y-%m-%d").date()

BASE = "https://discourse.onlinedegree.iitm.ac.in"
CATEGORY_ID = 34

# Your copied session cookie goes here
COOKIE = "_fbp=fb.2.1699285828091.2023810330; _ga_WMF1LS64VT=GS1.1.1744111996.1.1.1744112256.0.0.0; _gcl_au=1.1.988643992.1747750994; _ga=GA1.1.1833830032.1740290267; _ga_5HTJMW67XK=GS2.1.s1750258951$o513$g1$t1750258977$j34$l0$h0; _ga_08NPRH5L4M=GS2.1.s1750255854$o115$g1$t1750258998$j14$l0$h0; _t=KcJB9eSAhIhLmtfy8HP96E%2BPkHfLDP9WUBb3xMJwQshSXjqh3%2BOjZ6PYKUYJ5rCKn%2FOyKa8zKOXRSwDXpwBG0MLL%2BLU%2BGzHelh%2FW%2BMVqT7JEEGvF1wfg6jXZsIiE8Il57ps68Y9R4ila%2FdrZL2zVzs5lAIOiY%2Fr61OqqlyHJh5qyXPrmlXr24d8prRBxy3xekshC9kX%2FDMX%2Bs1%2BRJ6Di5%2FJOu9KbZIdTOGjnSa53yHmKQnSsP6dORS76VRI2XqQ25gkr%2B%2BFQ%2BH%2BM%2FA3mCaMYPLf4FrsEZbTcN7TQDI3T7nG2%2BVnhbw0oSfzDT0m4qoCW--yhSMY%2FkYWbiIurnU--tsCRJ666b8nooMSPnJqSNw%3D%3D; _forum_session=JuR%2B2wuYkZqt6OoxkenuFTetCgpBjL0nPQ1o4qa1WLwJtm3r6rF%2F%2F7EKK0znUhRjzGIg8gERw2UyNgPEJ2Z162seqKIbfjNqKYTTLWnamlIsvPeU3Z3lowRO8zYLpdSOhOXAltLuwj0kTCk4nyZYPeP9sXjaXlpWEKA06U2fxhEdN%2BwJK%2FXxI4RkyV%2F4TuONBbBnvbgZIjBK4fBHR0nWAu8woVYEVtil23luwQOQjUEK11M1jkxeydNBv1Y6EBpz45kjkrZSbWzUZZHYlrvpuW3TRUYXBQ%3D%3D--nWlCJhmhKNg47g7r--Y5dH033%2BTEDoKJpEyn9eqQ%3D%3D"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Referer": "https://discourse.onlinedegree.iitm.ac.in/",
    "Cookie": COOKIE
}

def fetch_topic_page(page):
    url = f"{BASE}/c/courses/tds-kb/{CATEGORY_ID}.json?page={page}"
    try:
        res = requests.get(url, headers=HEADERS)
        res.raise_for_status()
        return res.json().get("topic_list", {}).get("topics", [])
    except Exception as e:
        print(f"Error fetching page {page}: {e}")
        return []

def filter_topics(topics):
    filtered = []
    for t in topics:
        try:
            dt = parse(t['created_at']).date()
            # Fixed: proper date comparison instead of string comparison
            if START <= dt <= END:
                filtered.append({
                    'id': t['id'],
                    'title': t['title'],
                    'created_at': str(dt),
                    'url': f"{BASE}/t/{t['slug']}/{t['id']}"
                })
        except Exception as e:
            print(f"Error processing topic {t.get('id', 'unknown')}: {e}")
            continue
    return filtered

def scrape_all():
    page, all_posts = 0, []
    while True:
        print(f"Fetching topic list page {page}")
        topics = fetch_topic_page(page)
        if not topics:
            print("No more topics found, stopping...")
            break
        
        batch = filter_topics(topics)
        print(f"Found {len(batch)} topics in date range on page {page}")
        
        # Continue even if no topics in date range on this page
        # as there might be more on subsequent pages
        all_posts.extend(batch)
        page += 1
        time.sleep(1)  # Polite delay
        
        # Safety check to avoid infinite loops
        if page > 100:  # Adjust this limit as needed
            print("Reached maximum page limit, stopping...")
            break
    
    return all_posts

if __name__ == "__main__":
    print(f"Scraping topics from {START} to {END}")
    posts = scrape_all()
    
    # Save with corrected filename
    with open("discourse_posts.json", "w") as f:
        json.dump(posts, f, indent=2)
    
    print(f"✅ Saved {len(posts)} posts to 'discourse_posts.json'")
    
    # Print some sample data for verification
    if posts:
        print("\nSample posts:")
        for i, post in enumerate(posts[:3]):
            print(f"{i+1}. {post['title']} ({post['created_at']})")
