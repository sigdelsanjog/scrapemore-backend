from typing import List, Dict, Set
from bs4 import BeautifulSoup
import httpx
from urllib.parse import urljoin, urlparse
import re
import logging
import csv
from pathlib import Path

from app.config.driver import get_chrome_driver

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fetch_links(url: str, visited_links: Set[str]) -> List[str]:
    if url in visited_links:
         logger.info(f"Skipped fetching page (already visited): {url}")
         return []
    
    visited_links.add(url)
    driver = get_chrome_driver()

    try:
        logger.info(f"Fetching page: {url}")
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Extract and normalize all links from the page
        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        links = set(urljoin(base_url, a['href']) for a in soup.find_all('a', href=True))

        # Log each found link
        for link in links:
            logger.info(f"Found link: {link}")

        # Initialize sets to store unique URLs
        all_urls = set(links)
        pages = extract_unique_pages(all_urls)
        tags = extract_unique_tags(all_urls)
        categories = extract_unique_categories(all_urls)
        
        # Recursively explore pages, tags, and categories
        for page in pages:
            sub_links = await explore_sub_links(page['link'], visited_links)
            all_urls.update(sub_links)

        for tag in tags:
            sub_links = await explore_sub_links(tag['link'], visited_links)
            all_urls.update(sub_links)

        for category in categories:
            sub_links = await explore_sub_links(category['link'], visited_links)
            all_urls.update(sub_links)

        logger.info(f"Completed fetching links from: {url}")
        
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        
    finally:
        driver.quit()

    return list(all_urls)

async def explore_sub_links(url: str, visited_links: Set[str]) -> Set[str]:
    if url in visited_links:
      logger.info(f"Skipped exploring sub-links (already visited): {url}")
      return set()
    
    visited_links.add(url)
    driver = get_chrome_driver()
    """Explore sub-links under a given URL (e.g., pages, tags, categories)."""
    try:
        logger.info(f"Exploring sub-links for: {url}")
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        sub_links = set(urljoin(base_url, a['href']) for a in soup.find_all('a', href=True))

        # Log each found sub-link
        for link in sub_links:
            logger.info(f"Found sub-link: {link}")
    finally:
        driver.quit()

    return sub_links

def extract_unique_pages(urls: Set[str]) -> List[Dict[str, str]]:
    """Extract URLs with pagination."""
    pages = []
    page_pattern = re.compile(r'/pages?(/|$)', re.IGNORECASE)

    for url in urls:
        path = urlparse(url).path
        if page_pattern.search(path):
            segments = path.strip('/').split('/')
            if len(segments) > 1 and segments[0] in ['page', 'pages']:
                page_number = segments[1]
                if page_number.isdigit() and int(page_number) <= 100:
                    pages.append({
                        'category': 'Pages',
                        'link': url
                    })

    logger.info(f"Extracted pages: {pages}")
    return pages

def extract_unique_tags(urls: Set[str]) -> List[Dict[str, str]]:
    """Extract URLs with tags."""
    tags = []
    tag_pattern = re.compile(r'/tag/([^/]+)/?', re.IGNORECASE)

    for url in urls:
        match = tag_pattern.search(urlparse(url).path)
        if match:
            tag_name = match.group(1)
            tags.append({
                'category': f"Tag: {tag_name.capitalize()}",
                'link': url
            })

    logger.info(f"Extracted tags: {tags}")
    return tags

def extract_unique_categories(urls: Set[str]) -> List[Dict[str, str]]:
    """Extract URLs with categories."""
    categories = []
    category_pattern = re.compile(r'/category/([^/]+)/?', re.IGNORECASE)

    for url in urls:
        match = category_pattern.search(urlparse(url).path)
        if match:
            category_name = match.group(1)
            categories.append({
                'category': f"Category: {category_name.capitalize()}",
                'link': url
            })

    logger.info(f"Extracted categories: {categories}")
    return categories

async def scrape_content(urls: List[str]) -> Dict[str, Dict[str, str]]:
    results = {}
    for url in urls:
        logger.info(f"Scraping content from: {url}")
        response = await httpx.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        results[url] = {
            'title': soup.title.string if soup.title else 'No Title',
            'body': soup.body.get_text(strip=True) if soup.body else 'No Content'
        }
    return results

async def write_links_to_csv(links: List[str], filename: str = "unique_links.csv") -> str:
    """Write the list of links to a CSV file and return the filename."""
    filepath = Path(filename)
    with filepath.open(mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["URL"])
        for link in links:
            writer.writerow([link])
    return str(filepath)
