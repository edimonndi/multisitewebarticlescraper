import requests
from bs4 import BeautifulSoup

headers = {'User-Agent': 'Mozilla/5.0'}
base = 'https://1millionstories.net/minutes-before-my-brain-surgery-my-husband-leaned-close-and-admitted-your-friend-and-i-have-a-nine-year-old-daughter-he-was-counting-on-the-operation-erasing-my-memory-a/'

for p in range(1, 5):
    u = f"{base}?part={p}" if p > 1 else base
    r = requests.get(u, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    entry = soup.find('div', class_='entry-content') or soup.find('article')
    paras = [p.get_text(strip=True) for p in entry.find_all('p') if len(p.get_text(strip=True)) > 20] if entry else []
    print(f'Part {p}: status={r.status_code}, paras={len(paras)}')
    if paras:
        print('  First:', paras[0][:60])
        print('  Last:', paras[-1][:60])
