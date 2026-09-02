import requests
from bs4 import BeautifulSoup

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}

def inspect(u):
    print('=== URL:', u)
    r = requests.get(u, headers=headers, timeout=12)
    print('Status:', r.status_code)
    soup = BeautifulSoup(r.text, 'html.parser')
    print('Title:', soup.title.get_text() if soup.title else 'No Title')
    print('H1:', [h.get_text(strip=True) for h in soup.find_all('h1')])
    print('Total P tags in page:', len(soup.find_all('p')))
    for p in soup.find_all('p')[:5]:
        print('  P:', p.get_text(strip=True)[:100])
    print('Containers:')
    for div in soup.find_all(['div', 'article', 'section', 'main']):
        classes = div.get('class', [])
        cid = div.get('id', '')
        if any(w in str(classes).lower() or w in str(cid).lower() for w in ['content', 'post', 'entry', 'story', 'article', 'body', 'text', 'detail']):
            paras = div.find_all('p')
            if len(paras) > 3:
                print(f'   Tag <{div.name}> id="{cid}" class="{classes}" -> {len(paras)} paragraphs')
    print('-'*50)

inspect('https://kaylestore.net/my-husband-reserved-seats-7a-and-7b-to-escape-with-another-woman-but-he-forgot-that-after-12-years-i-knew-every-one-of-his-lies/')
inspect('https://tv.topthuysinh.com/part-2-my-soon-to-be-husband-unintentionally-left-our-phone-line-open-and-i-listened-in-on-a-conversation-he-was-having-with-his-relatives-about-me5-019/')
