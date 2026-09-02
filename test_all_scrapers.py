import requests
import re
import html
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, parse_qs, urlencode, urlunparse

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

def clean_text(text: str) -> str:
    if not text:
        return ''
    text = html.unescape(text)
    # Fix unicode replacements
    replacements = {
        '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"',
        '\u2014': '—', '\u2013': '–', '\u2026': '...', '\u00a0': ' ',
        '': "'"
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

def extract_story_from_soup(soup: BeautifulSoup):
    # Extract clean title
    title = ''
    og_title = soup.find('meta', property='og:title')
    if og_title and og_title.get('content'):
        title = og_title['content'].strip()
    
    if not title and soup.title:
        title = soup.title.get_text(strip=True)
    
    if not title:
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text(strip=True)
            
    # Clean title
    if title:
        title = re.sub(r'\s*[-|–—]\s*(America Focus|Fanstopis|LEVANEWS|Human Heart Tales).*$', '', title, flags=re.IGNORECASE)
        title = re.sub(r'^(FULL STORY|Part \d+|Story)\s*[-:–—]\s*', '', title, flags=re.IGNORECASE).strip()
        title = clean_text(title)
    
    # Extract content container
    content_area = (
        soup.find('div', class_=re.compile(r'(entry-content|post-content|article-content|story-content|elementor-widget-theme-post-content)'))
        or soup.find('article')
        or soup.find('main')
    )
    if not content_area:
        return title, []
        
    # Make a copy to mutate
    content_area = BeautifulSoup(str(content_area), 'html.parser')
    
    # Remove unwanted elements
    for tag in content_area.find_all([
        'script', 'style', 'ins', 'nav', 'aside', 'figure', 'iframe', 'noscript', 'form', 'button', 'svg'
    ]):
        tag.decompose()
        
    for tag in content_area.find_all(class_=re.compile(r'(ad|banner|share|social|author|related|paginate|navigation|popup|widget|wp-block-buttons|post-page-numbers|comment)', re.IGNORECASE)):
        tag.decompose()
        
    for tag in content_area.find_all(id=re.compile(r'(ad|banner|share|social|author|related|comments)', re.IGNORECASE)):
        tag.decompose()

    paragraphs = []
    for p in content_area.find_all(['p', 'blockquote']):
        txt = clean_text(p.get_text(separator=' ', strip=True))
        if not txt:
            continue
        lower_txt = txt.lower()
        if len(txt) < 15 and ('next' in lower_txt or 'continue' in lower_txt or 'page' in lower_txt or 'part' in lower_txt):
            continue
        if any(lower_txt.startswith(bad) for bad in [
            'advertisement', 'read more', 'click here', 'author bio', 'written by', 'subscribe to',
            'share on', 'source:', 'photo by', 'image by', 'sponsored'
        ]):
            continue
        if 'is a contributor who enjoys writing' in lower_txt or 'contributor who enjoys writing about' in lower_txt:
            continue
        paragraphs.append(txt)
        
    return title, paragraphs

if __name__ == '__main__':
    tests = [
        'https://america-focus.com/a-battered-suitcase-on-my-kitchen-floor-ended-my-twenty-three-year-marriage/',
        'https://humanhearttales.feji.io/full-story-she-stole-my-wedding-dress-then-the-security-footage-started-playing/',
        'https://fanstopis.com/my-wife-was-about-to-be-burie',
        'https://levanews.com/hours-after-my-divorce-became-final-my-former-mother-in-law-tried-to-charge-a-48000-auction-purchase-to-my-credit-card-but-i-had-already-canceled-it-by-the-next-morning-my-ex-husband-was-having/'
    ]
    for url in tests:
        print(f'Fetching {url} ...')
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        t, p = extract_story_from_soup(soup)
        print(f'Title: {t}')
        print(f'Paragraphs count: {len(p)}')
        if p:
            print(f'  First: {p[0][:70]}')
            print(f'  Last:  {p[-1][:70]}')
        print('-'*50)
