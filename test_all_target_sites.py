import requests
from scraper_engine import StoryScraper

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
    ("AmoMedia (1 part)", "https://amomedia.com/661995-my-fiancee-kept-assuring-me-that-she.html"),
]

scraper = StoryScraper()

for name, url in test_urls:
    try:
        article = scraper.scrape(url)
        print(f"[{name}]")
        print(f"  SUCCESS! | Title: {article.title[:55]}... | Parts: {article.total_parts} | Words: {article.total_words:,}")
        if article.parts and article.parts[0].paragraphs:
            print(f"  First: {article.parts[0].paragraphs[0][:60]}...")
            print(f"  Last:  {article.parts[-1].paragraphs[-1][:60]}...")
    except Exception as e:
        print(f"[{name}] FAILED: {e}")
    print("-" * 50)
