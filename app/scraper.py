import asyncio
from typing import List, Dict
from bs4 import BeautifulSoup
import httpx
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from urllib.parse import urlparse

def extract_unique_categories(urls):
    categories = set()
    for url in urls:
        path = urlparse(url).path
        segments = path.strip('/').split('/')
        if segments:
            categories.add(segments[0].capitalize())
    return list(categories)


async def fetch_links(url: str) -> List[str]:
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    
    driver = webdriver.Chrome(options=options)
    
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    links = set(a.get('href') for a in soup.find_all('a', href=True))
    
    driver.quit()
    
    return list(links)

async def scrape_content(urls: List[str]) -> Dict[str, Dict[str, str]]:
    results = {}
    for url in urls:
        response = await httpx.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        results[url] = {
            'title': soup.title.string if soup.title else 'No Title',
            'body': soup.body.get_text(strip=True) if soup.body else 'No Content'
        }
    return results
