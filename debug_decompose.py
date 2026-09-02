import requests
import re
from bs4 import BeautifulSoup

url = 'https://kaylestore.net/my-husband-reserved-seats-7a-and-7b-to-escape-with-another-woman-but-he-forgot-that-after-12-years-i-knew-every-one-of-his-lies/'
headers = {'User-Agent': 'Mozilla/5.0'}
r = requests.get(url, headers=headers)
soup = BeautifulSoup(r.text, 'html.parser')

content_area = (
    soup.find("div", class_=re.compile(r"(entry-content|post-content|article-content|story-content|elementor-widget-theme-post-content)"))
    or soup.find("article")
    or soup.find("main")
)

print('content_area tag:', content_area.name, content_area.get('class'))
print('Number of p tags BEFORE decompose:', len(content_area.find_all('p')))

container = BeautifulSoup(str(content_area), "html.parser")

for tag in list(container.find_all([
    "script", "style", "ins", "nav", "aside", "figure", "iframe", "noscript",
    "form", "button", "svg", "header", "footer", "select", "option"
])):
    tag.decompose()

print('Number of p tags after script/style:', len(container.find_all('p')))

for tag in list(container.find_all(class_=re.compile(r"(ad|banner|share|social|author|related|paginate|navigation|popup|widget|wp-block-buttons|post-page-numbers|comment|disclaimer|tags|meta)", re.IGNORECASE))):
    p_in_tag = len(tag.find_all('p'))
    if p_in_tag > 0:
        print(f"DECOMPOSING tag <{tag.name}> class={tag.get('class')} with {p_in_tag} paragraphs!")
    tag.decompose()

print('Number of p tags after class regex:', len(container.find_all('p')))
