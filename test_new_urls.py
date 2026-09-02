from scraper_engine import StoryScraper

urls = [
    'https://kaylestore.net/my-husband-reserved-seats-7a-and-7b-to-escape-with-another-woman-but-he-forgot-that-after-12-years-i-knew-every-one-of-his-lies/',
    'https://leadtohappiness.com/find-your-own-way-home-seven-months-pregnant-my-husband-abandoned-me-at-the-airport-and-flew-to-paris-with-his-mistress-until-a-gate-agent-found-the-passport-he-had-reporte/',
    'https://tv.topthuysinh.com/part-2-my-soon-to-be-husband-unintentionally-left-our-phone-line-open-and-i-listened-in-on-a-conversation-he-was-having-with-his-relatives-about-me5-019/',
    'https://kaylestore.net/where-did-you-learn-that-song-i-asked-the-17-year-old-stranger-who-soothed-my-newborn-daughter-on-a-flight-with-a-lullaby-only-my-late-wife-ever-sang-he-fell-silent-then-a/',
    'https://1millionstories.net/minutes-before-my-brain-surgery-my-husband-leaned-close-and-admitted-your-friend-and-i-have-a-nine-year-old-daughter-he-was-counting-on-the-operation-erasing-my-memory-a/',
    'https://happysoulshop.com/we-adopted-a-girl-in-a-wheelchair-but-her-first-words-about-our-basement-left-us-frozen/'
]

s = StoryScraper()
for u in urls:
    print('Testing:', u)
    try:
        art = s.scrape(u, progress_callback=lambda msg, p, t, pct: print(f'   [Prog] {msg}'))
        print(f'  SUCCESS: Title="{art.title[:60]}...", Parts={art.total_parts}, Words={art.total_words}')
        if art.parts:
            print(f'  First para: {art.parts[0].paragraphs[0][:70]}...')
            print(f'  Last para:  {art.parts[-1].paragraphs[-1][:70]}...')
    except Exception as e:
        print('  ERROR:', e)
    print('-'*50)
