import requests
import re
import html
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, parse_qs, urlencode, urlunparse
import time

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

def clean_text(text: str) -> str:
    if not text:
        return ''
    text = html.unescape(text)
    replacements = {
        '\u2018': "'", '\u2019': "'", '\u201a': "'", '\u201b': "'",
        '\u201c': '"', '\u201d': '"', '\u201e': '"', '\u201f': '"',
        '\u2014': '—', '\u2013': '–', '\u2026': '...', '\u00a0': ' ',
        '\ufeff': '', '\u200b': '', '\u200e': '', '\u200f': ''
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

def extract_story_from_soup(soup: BeautifulSoup):
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
            
    if title:
        title = re.sub(r'\s*[-|–—]\s*(America Focus|Fanstopis|LEVANEWS|Human Heart Tales|DAILY STORIES).*$', '', title, flags=re.IGNORECASE)
        title = re.sub(r'^(FULL STORY|Part \d+|Story)\s*[-:–—]\s*', '', title, flags=re.IGNORECASE).strip()
        title = clean_text(title)
    
    content_area = (
        soup.find('div', class_=re.compile(r'(entry-content|post-content|article-content|story-content|elementor-widget-theme-post-content)'))
        or soup.find('article')
        or soup.find('main')
    )
    if not content_area:
        return title, []
        
    content_area = BeautifulSoup(str(content_area), 'html.parser')
    
    for tag in content_area.find_all([
        'script', 'style', 'ins', 'nav', 'aside', 'figure', 'iframe', 'noscript', 'form', 'button', 'svg', 'header', 'footer'
    ]):
        tag.decompose()
        
    for tag in content_area.find_all(class_=re.compile(r'(ad|banner|share|social|author|related|paginate|navigation|popup|widget|wp-block-buttons|post-page-numbers|comment|disclaimer)', re.IGNORECASE)):
        tag.decompose()
        
    for tag in content_area.find_all(id=re.compile(r'(ad|banner|share|social|author|related|comments)', re.IGNORECASE)):
        tag.decompose()

    paragraphs = []
    for p in content_area.find_all(['p', 'blockquote']):
        txt = clean_text(p.get_text(separator=' ', strip=True))
        if not txt:
            continue
        lower_txt = txt.lower()
        if len(txt) < 15 and any(k in lower_txt for k in ['next', 'continue', 'page', 'part', 'prev', 'previous', 'share']):
            continue
        if any(lower_txt.startswith(bad) for bad in [
            'advertisement', 'read more', 'click here', 'author bio', 'written by', 'subscribe to',
            'share on', 'source:', 'photo by', 'image by', 'sponsored', 'leave a reply', 'comment'
        ]):
            continue
        if 'is a contributor who enjoys writing' in lower_txt or 'contributor who enjoys writing about' in lower_txt:
            continue
        paragraphs.append(txt)
        
    return title, paragraphs

def detect_site_and_scrape(url: str, progress_cb=None):
    session = requests.Session()
    session.headers.update(HEADERS)
    
    url = url.strip()
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    story_title = ''
    all_parts = []
    seen_hashes = set()
    seen_urls = set()
    
    # Strategy 1: Feji / Human Heart Tales slug style: full-story-... or part-N-...
    if 'feji.io' in domain or re.search(r'/(full-story-|part-\d+-)', parsed.path, re.IGNORECASE):
        # Extract base slug
        path = parsed.path.strip('/')
        slug = path.rsplit('/', 1)[-1]
        if slug.lower().startswith('full-story-'):
            base_suffix = slug[len('full-story-'):]
            current_part = 1
        elif re.match(r'^part-(\d+)-', slug, re.IGNORECASE):
            m = re.match(r'^part-(\d+)-(.+)$', slug, re.IGNORECASE)
            current_part = int(m.group(1))
            base_suffix = m.group(2)
        else:
            base_suffix = slug
            current_part = 1
            
        while True:
            if current_part == 1:
                target_url = f"{parsed.scheme}://{parsed.netloc}/full-story-{base_suffix}/"
            else:
                target_url = f"{parsed.scheme}://{parsed.netloc}/part-{current_part}-{base_suffix}/"
                
            if target_url in seen_urls:
                break
            seen_urls.add(target_url)
            
            if progress_cb:
                progress_cb(f"Scraping part {current_part}...")
                
            try:
                r = session.get(target_url, timeout=12, allow_redirects=True)
                if r.status_code == 404 or r.status_code != 200:
                    # If part 1 with full-story- didn't work, try part-1-
                    if current_part == 1 and r.status_code == 404:
                        alt_url = f"{parsed.scheme}://{parsed.netloc}/part-1-{base_suffix}/"
                        r = session.get(alt_url, timeout=12, allow_redirects=True)
                        if r.status_code != 200:
                            break
                    else:
                        break
                r.encoding = r.apparent_encoding or 'utf-8'
                soup = BeautifulSoup(r.text, 'html.parser')
                title, paras = extract_story_from_soup(soup)
                if not story_title and title:
                    story_title = title
                if not paras:
                    break
                
                content_joined = "\n\n".join(paras)
                content_hash = hash(content_joined[:300] + content_joined[-300:])
                if content_hash in seen_hashes:
                    break
                seen_hashes.add(content_hash)
                
                all_parts.append({
                    'part_num': current_part,
                    'url': target_url,
                    'paragraphs': paras
                })
                current_part += 1
            except Exception as e:
                print(f"Error on feji part {current_part}: {e}")
                break

    # Strategy 2: Query param pagination (e.g. ?part=2 or ?page=2) used by Fanstopis, Levanews, etc.
    elif 'fanstopis.com' in domain or 'levanews.com' in domain or 'part=' in parsed.query:
        # Base url without ?part query
        base_clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}/"
        current_part = 1
        
        while True:
            if current_part == 1:
                target_url = base_clean
            else:
                target_url = f"{base_clean}?part={current_part}"
                
            if target_url in seen_urls:
                break
            seen_urls.add(target_url)
            
            if progress_cb:
                progress_cb(f"Scraping part {current_part}...")
                
            try:
                r = session.get(target_url, timeout=12, allow_redirects=True)
                if r.status_code != 200:
                    break
                r.encoding = r.apparent_encoding or 'utf-8'
                soup = BeautifulSoup(r.text, 'html.parser')
                title, paras = extract_story_from_soup(soup)
                if not story_title and title:
                    story_title = title
                if not paras:
                    break
                    
                content_joined = "\n\n".join(paras)
                content_hash = hash(content_joined[:300] + content_joined[-300:])
                if content_hash in seen_hashes:
                    # Same content returned (end of parts)
                    break
                seen_hashes.add(content_hash)
                
                all_parts.append({
                    'part_num': current_part,
                    'url': target_url,
                    'paragraphs': paras
                })
                current_part += 1
            except Exception as e:
                print(f"Error on part {current_part}: {e}")
                break

    # Strategy 3: Slash pagination (e.g. /2/, /3/) used by America-Focus and WordPress multi-page posts
    else:
        # Normalize base URL by stripping trailing /<number>/
        clean_path = re.sub(r'/\d+/?$', '', parsed.path).rstrip('/')
        base_clean = f"{parsed.scheme}://{parsed.netloc}{clean_path}/"
        current_part = 1
        
        while current_part <= 200:  # Safety upper bound
            if current_part == 1:
                target_url = base_clean
            else:
                target_url = f"{base_clean}{current_part}/"
                
            if target_url in seen_urls:
                break
            seen_urls.add(target_url)
            
            if progress_cb:
                progress_cb(f"Scraping part {current_part}...")
                
            try:
                r = session.get(target_url, timeout=12, allow_redirects=True)
                if r.status_code != 200:
                    break
                # Check if server redirected back to base_clean on page > 1 (WordPress loopback)
                final_url = r.url.rstrip('/') + '/'
                if current_part > 1 and final_url == base_clean:
                    break
                    
                r.encoding = r.apparent_encoding or 'utf-8'
                soup = BeautifulSoup(r.text, 'html.parser')
                title, paras = extract_story_from_soup(soup)
                if not story_title and title:
                    story_title = title
                if not paras:
                    break
                    
                content_joined = "\n\n".join(paras)
                content_hash = hash(content_joined[:300] + content_joined[-300:])
                if content_hash in seen_hashes:
                    break
                seen_hashes.add(content_hash)
                
                all_parts.append({
                    'part_num': current_part,
                    'url': target_url,
                    'paragraphs': paras
                })
                current_part += 1
            except Exception as e:
                print(f"Error on part {current_part}: {e}")
                break

    return story_title, all_parts

if __name__ == '__main__':
    def prog(msg):
        print(f"  [Progress] {msg}")

    print("=== Testing Fanstopis ===")
    t, parts = detect_site_and_scrape('https://fanstopis.com/my-wife-was-about-to-be-burie', prog)
    print(f"Title: {t}, Total parts scraped: {len(parts)}")
    
    print("\n=== Testing Levanews ===")
    t, parts = detect_site_and_scrape('https://levanews.com/hours-after-my-divorce-became-final-my-former-mother-in-law-tried-to-charge-a-48000-auction-purchase-to-my-credit-card-but-i-had-already-canceled-it-by-the-next-morning-my-ex-husband-was-having/', prog)
    print(f"Title: {t}, Total parts scraped: {len(parts)}")

    print("\n=== Testing Feji ===")
    t, parts = detect_site_and_scrape('https://humanhearttales.feji.io/full-story-she-stole-my-wedding-dress-then-the-security-footage-started-playing/', prog)
    print(f"Title: {t}, Total parts scraped: {len(parts)}")
