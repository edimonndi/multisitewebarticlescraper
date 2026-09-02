import requests
from bs4 import BeautifulSoup
from test_improvements import extract_from_soup_improved, clean_pure_text

test_urls = [
    ("America Focus (97 parts)", "https://america-focus.com/a-battered-suitcase-on-my-kitchen-floor-ended-my-twenty-three-year-marriage/"),
    ("Feji (9 parts)", "https://humanhearttales.feji.io/full-story-she-stole-my-wedding-dress-then-the-security-footage-started-playing/"),
    ("Fanstopis (3 parts)", "https://fanstopis.com/my-wife-was-about-to-be-burie"),
    ("Levanews (3 parts)", "https://levanews.com/hours-after-my-divorce-became-final-my-former-mother-in-law-tried-to-charge-a-48000-auction-purchase-to-my-credit-card-but-i-had-already-canceled-it-by-the-next-morning-my-ex-husband-was-having/"),
    ("Kayle Store 1 (1 part)", "https://kaylestore.net/my-husband-reserved-seats-7a-and-7b-to-escape-with-another-woman-but-he-forgot-that-after-12-years-i-knew-every-one-of-his-lies/"),
    ("Kayle Store 2 (1 part)", "https://kaylestore.net/where-did-you-learn-that-song-i-asked-the-17-year-old-stranger-who-soothed-my-newborn-daughter-on-a-flight-with-a-lullaby-only-my-late-wife-ever-sang-he-fell-silent-then-a/"),
    ("Lead to Happiness (1 part)", "https://leadtohappiness.com/find-your-own-way-home-seven-months-pregnant-my-husband-abandoned-me-at-the-airport-and-flew-to-paris-with-his-mistress-until-a-gate-agent-found-the-passport-he-had-reporte/"),
    ("Top Thuy Sinh (1 part)", "https://tv.topthuysinh.com/part-2-my-soon-to-be-husband-unintentionally-left-our-phone-line-open-and-i-listened-in-on-a-conversation-he-was-having-with-his-relatives-about-me5-019/"),
    ("1 Million Stories (3 parts)", "https://1millionstories.net/minutes-before-my-brain-surgery-my-husband-leaned-close-and-admitted-your-friend-and-i-have-a-nine-year-old-daughter-he-was-counting-on-the-operation-erasing-my-memory-a/"),
    ("Happy Soul Shop (1 part)", "https://happysoulshop.com/we-adopted-a-girl-in-a-wheelchair-but-her-first-words-about-our-basement-left-us-frozen/"),
]

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}

for name, url in test_urls:
    r = requests.get(url, headers=headers, timeout=12)
    soup = BeautifulSoup(r.text, 'html.parser')
    title, paras = extract_from_soup_improved(soup)
    print(f"[{name}]")
    print(f"  Status: {r.status_code} | Title: {title[:60]}... | Paras: {len(paras)}")
    if paras:
        print(f"  First: {paras[0][:60]}...")
        print(f"  Last:  {paras[-1][:60]}...")
    else:
        print("  FAILED TO EXTRACT PARAS!")
    print("-" * 50)
