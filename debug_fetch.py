import re
import requests
from bs4 import BeautifulSoup

urls = [
    'https://humanhearttales.feji.io/full-story-she-stole-my-wedding-dress-then-the-security-footage-started-playing/',
    'https://humanhearttales.feji.io/part-2-she-stole-my-wedding-dress-then-the-security-footage-started-playing/',
    'https://humanhearttales.feji.io/part-3-she-stole-my-wedding-dress-then-the-security-footage-started-playing/',
    'https://humanhearttales.feji.io/part-4-she-stole-my-wedding-dress-then-the-security-footage-started-playing/',
    'https://humanhearttales.feji.io/part-9-she-stole-my-wedding-dress-then-the-security-footage-started-playing/'
]

for u in urls:
    r = requests.get(u, timeout=20)
    print('URL:', u)
    print('STATUS:', r.status_code)
    print('FINAL:', r.url)
    soup = BeautifulSoup(r.text, 'html.parser')
    h = soup.find('h1')
    print('H1:', h.get_text(' ', strip=True)[:150] if h else 'NO_H1')
    c = soup.find('article') or soup.find('main') or soup.find('div', class_=re.compile(r'entry-content|post-content|article-content|story-content'))
    print('HAS_CONTENT_AREA:', bool(c))
    if c:
        parts = []
        for p in c.find_all('p'):
            t = p.get_text(' ', strip=True)
            if len(t) > 20 and not t.lower().startswith('advertisement') and not t.lower().startswith('read more'):
                parts.append(t)
        print('PARA_COUNT:', len(parts))
        for i, t in enumerate(parts[:3], 1):
            print(f'Para{i}:', t[:180])
    print('---')
