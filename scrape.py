import requests
import json
from dateutil.parser import parse
import time
from datetime import datetime

START = datetime.strptime('2025-01-01', "%Y-%m-%d").date()
END   = datetime.strptime('2025-04-14', "%Y-%m-%d").date()


BASE = "https://discourse.onlinedegree.iitm.ac.in"
CATEGORY_ID = 34
START, END = '2025-01-01', '2025-04-14'

# 👇 Your copied session cookie goes here
COOKIE = "_fbp=fb.2.1699285828091.2023810330; _ga_WMF1LS64VT=GS1.1.1744111996.1.1.1744112256.0.0.0; _gcl_au=1.1.988643992.1747750994; _ga=GA1.1.1833830032.1740290267; _ga_5HTJMW67XK=GS2.1.s1750258951$o513$g1$t1750258977$j34$l0$h0; _ga_08NPRH5L4M=GS2.1.s1750255854$o115$g1$t1750258998$j14$l0$h0; _t=lQaA422lwhssuGXjIYeSbNbYqqhKpheO1cttk4cNnDIOSbQU5gH1083z3UrxpoGDJOe68UQ4HmlPd9IZ2KEOjoK7kQN96E05%2BmNEQjOAEJz7b%2FCTYWsVZEk71jFDl9KLyMmvUT8oUerryzpKTNhhq%2FIgSvuVZ1PtumC4BRJt8sgfNTRKVUpA9BKr9saWGVqObz%2BvFIGSmbt4TPv9Jg3bSyrwA1%2B0L1vB%2FWkURo4cJHsfm5bNUZmhT6NUfJ0CjrtOaunrWiYPI%2BXL65PLcddMMr66sBm2hONQc%2BA7pl8W1FRDovo%2BBSpUk0bFMfN5GkF6--oAeHT5%2F4FvlKod65--sxRYTRBa6pMPEaD4Vki5RA%3D%3D; _forum_session=zJWVQhAmJUdxh6jU3jKfnCHKbvUB6rAzXashvP9NwKzbNOKZEWvQRxnxThyfwCoAAk%2BHVB67%2FtDZ0dDZelnFXILRawRT0cbM0PrM6k%2FgLCG%2FSjv3F%2BNSyQ9k%2FAO%2FMB%2F%2FgbsQHfRewbMSrVopLl3uB2MfCLwQ1jUawmuWUoxvaWLkTB%2B9tBya9tSyp6bsHvdWTrUI%2B9ynLAMyf15OF4VAY%2BJT7baFySMGkGVKznmPyov%2Bnmnqe%2FXDgxjl2pEIy3knDqshKJDAu1IxV6%2FyXLmFzXfjIufMkA%3D%3D--ht21KhM%2BuitmVDqF--WrpmiVCioHmt51faWJJ2rg%3D%3D"
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
    global START
    global END
    for t in topics:
        try:
            dt = parse(t['created_at']).date()
            if START <= str(dt) <= END:
                filtered.append({
                    'id': t['id'],
                    'title': t['title'],
                    'created_at': str(dt),
                    'url': f"{BASE}/t/{t['slug']}/{t['id']}"
                })
        except Exception:
            continue
    return filtered

def scrape_all():
    page, all_posts = 0, []
    while True:
        print(f"Fetching topic list page {page}")
        topics = fetch_topic_page(page)
        if not topics:
            break
        batch = filter_topics(topics)
        '''if not batch:
            break'''
        all_posts.extend(batch)
        page += 1
        time.sleep(1)  # polite delay
    return all_posts

if __name__ == "__main__":
    posts = scrape_all()
    with open("discourse_posts.json", "w") as f:
        json.dump(posts, f, indent=2)
    print(f"✅ Saved {len(posts)} posts to 'discourse_posts.json'")