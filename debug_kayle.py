import requests
from bs4 import BeautifulSoup
from scraper_engine import StoryScraper

url = 'https://kaylestore.net/my-husband-reserved-seats-7a-and-7b-to-escape-with-another-woman-but-he-forgot-that-after-12-years-i-knew-every-one-of-his-lies/'
s = StoryScraper()
soup, final_url, status = s.fetch_page(url)
print('status:', status, 'soup:', bool(soup))
title, paras = s.extract_from_soup(soup)
print('title:', title)
print('paras count:', len(paras))
if paras:
    print('para 0:', paras[0])
    print('para -1:', paras[-1])
