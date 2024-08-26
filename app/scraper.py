import asyncio
from typing import List, Dict
from bs4 import BeautifulSoup
import httpx
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlparse
from webdriver_manager.chrome import ChromeDriverManager
import re
from typing import List, Dict

def extract_pages(urls: List[str]) -> List[Dict[str, str]]:
    pages = []
    page_pattern = re.compile(r'/pages?(/|$)', re.IGNORECASE)
    
    for url in urls:
        parsed_url = urlparse(url)
        path = parsed_url.path
        if page_pattern.search(path):
            segments = path.strip('/').split('/')
            if len(segments) > 1 and segments[0].lower() in ['page', 'pages']:
                page_number = segments[1]
                if page_number.isdigit() and int(page_number) <= 100:
                    pages.append({
                        'category': 'Pages',
                        'link': f"{parsed_url.scheme}://{parsed_url.netloc}{path}"
                    })
    
    return pages

def extract_tags(urls: List[str]) -> List[Dict[str, str]]:
    tags = []
    tag_pattern = re.compile(r'/tags?(/|$)', re.IGNORECASE)

    for url in urls:
        parsed_url = urlparse(url)
        path = parsed_url.path
        if tag_pattern.search(path):
            segments = path.strip('/').split('/')
            if len(segments) > 1:
                tag_name = segments[1]
                tags.append({
                    'category': 'Tag',
                    'link': f"{parsed_url.scheme}://{parsed_url.netloc}/{segments[0]}/{tag_name}"
                })

    return tags

def extract_years(urls: List[str]) -> List[Dict[str, str]]:
    years = []
    year_pattern = re.compile(r'/\d{4}(/|$)')

    for url in urls:
        parsed_url = urlparse(url)
        path = parsed_url.path
        match = year_pattern.search(path)
        if match:
            year_segment = match.group().strip('/')
            years.append({
                'category': year_segment,
                'link': f"{parsed_url.scheme}://{parsed_url.netloc}{path}"
            })

    return years

def analyze_patterns(urls: List[str]) -> Dict[str, List[Dict[str, str]]]:
    results = {
        'Pages': extract_pages(urls),
        'Tags': extract_tags(urls),
        'Years': extract_years(urls),
    }

    return results



def extract_unique_categories(urls: List[str]) -> List[Dict[str, str]]:
    categories = set()
    for url in urls:
        path = urlparse(url).path
        segments = path.strip('/').split('/')
        for segment in segments:
            words = segment.split('-')
            # Include segments with one or two words
            if 1 <= len(words) <= 2:
                categories.add(segment.lower())

    # Assuming the domain should be derived from the URLs provided
    if urls:
        domain = urlparse(urls[0]).scheme + "://" + urlparse(urls[0]).netloc
    else:
        domain = ""

    return [{'category': cat.capitalize(), 'link': f"{domain}/{cat.lower()}"} for cat in categories]


def extract_unique_pages(urls: List[str]) -> List[Dict[str, str]]:
    pages = []
    page_pattern = re.compile(r'/pages?(/|$)', re.IGNORECASE)
    
    for url in urls:
        path = urlparse(url).path
        if page_pattern.search(path):
            segments = path.strip('/').split('/')
            if len(segments) > 1 and segments[0].lower() in ['page', 'pages']:
                page_number = segments[1]
                if page_number.isdigit() and int(page_number) <= 100:
                    pages.append({
                        'category': f"{segments[0].capitalize()} {page_number}",
                        'link': f"{urlparse(url).scheme}://{urlparse(url).netloc}{path}"
                    })
    
    return pages


async def fetch_links(url: str) -> List[str]:
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--no-sandbox")  # Disable sandboxing for headless environments
    options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems

    # Set up ChromeDriver
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
