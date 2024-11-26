from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from config.models import URLRequest, URLResponse, URLListRequest
from scraper import fetch_links, write_links_to_csv, extract_unique_categories, extract_unique_pages, extract_unique_tags
import logging
import sys
import os
import json
import asyncio
import aiohttp
from aiohttp import ClientError, ClientTimeout

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from packages.pdfextract.routes import router as pdf_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.include_router(pdf_router, prefix="/pdfextract", tags=["PDF Extraction"])


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define constants
TIMEOUT = 10  # Timeout for each URL request in seconds

@app.post("/scrape-unique-links-in-categories/", response_model=dict)
async def scrape_unique_links_in_categories(request: URLListRequest, background_tasks: BackgroundTasks):
    """
    Fetch all URLs from each category page and then scrape their contents concurrently.
    """
    try:
        if not request.urls:
            raise ValueError("No category URLs provided in the request.")
        logger.info(f"Scraping the following categories: {request.urls}")

        categories_with_links = {}
        for category_url in request.urls:
            logger.info(f"Fetching links from category URL: {category_url}")
            
            # Fetch all links within the category page only once
            category_links = await fetch_links(category_url, set())
            logger.info(f"Found {len(category_links)} links in {category_url}")

            # Enumerate the links found
            urls_to_scrape = [link['link'] for link in category_links if isinstance(link, dict) and 'link' in link]
            logger.info(f"URLs to scrape from {category_url}: {urls_to_scrape}")

            if not urls_to_scrape:
                logger.warning(f"No URLs found to scrape for category: {category_url}")

            # Scrape contents of all URLs found within the category concurrently
            scraped_contents = await asyncio.gather(
                *[scrape_single_url(url) for url in urls_to_scrape],
                return_exceptions=True  # Capture errors individually
            )

            # Store results in the dictionary
            categories_with_links[category_url] = {}
            for result in scraped_contents:
                if isinstance(result, tuple) and len(result) == 2:
                    url, content = result
                    categories_with_links[category_url][url] = content
                    logger.info(f"Scraped content from {url}")
                elif isinstance(result, Exception):
                    logger.error(f"Error scraping URL: {result}")

        # Check if any content was scraped successfully
        if not categories_with_links:
            raise ValueError("No content could be scraped from the provided URLs.")

        # Save the scraped contents into a JSON file
        json_file_path = "output.json"
        with open(json_file_path, "w") as json_file:
            json.dump(categories_with_links, json_file, indent=4)

        # Clean up the JSON file after the response
        background_tasks.add_task(clean_up_file, json_file_path)
        return FileResponse(
            path=json_file_path, filename="output.json", media_type="application/json"
        )
    except Exception as e:
        logger.error(f"Error scraping unique links in categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to scrape unique links in categories.")

@app.post("/analyze", response_model=URLResponse)
async def analyze_url(request: URLRequest):
    try:
        visited_links = set()
        all_links = await fetch_links(request.url, visited_links)

        pages = extract_unique_pages(all_links)
        tags = extract_unique_tags(all_links)
        categories = extract_unique_categories(all_links)

        response_urls = []
        for page in pages:
            response_urls.append({"category": "Page", "url": page['link']})
        for tag in tags:
            response_urls.append({"category": tag['category'], "url": tag['link']})
        for category in categories:
            response_urls.append({"category": category['category'], "url": category['link']})

        logger.info(f"Prepared response: {response_urls}")
        return {"urls": response_urls}
    except Exception as e:
        logger.error(f"Error in /analyze: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scrape-links/")
async def scrape_links(request: URLListRequest, background_tasks: BackgroundTasks):
    """
    Fetch and scrape links based on the provided list of URLs.
    """
    try:
        urls = request.urls
        visited_links = set()
        logger.info(f"Scraping the following URLs: {urls}")

        all_links = []
        for url in urls:
            links = await fetch_links(url, visited_links)
            all_links.extend(links)

        csv_file_path = await write_links_to_csv(all_links)
        background_tasks.add_task(clean_up_file, csv_file_path)
        return FileResponse(path=csv_file_path, filename="unique_links.csv", media_type="text/csv")
    except Exception as e:
        logger.error(f"Error scraping links: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error scraping links: {str(e)}")

@app.post("/scrape-all-urls/")
async def scrape_all_urls(request: URLListRequest, background_tasks: BackgroundTasks):
    """
    Scrape the contents of multiple URLs concurrently and save them into a JSON file.
    """
    try:
        if not request.urls:
            raise ValueError("No URLs provided in the request.")
        logger.info(f"Starting to scrape the following URLs: {request.urls}")

        results = await asyncio.gather(
            *[scrape_single_url(url) for url in request.urls],
            return_exceptions=True
        )

        url_contents = {}
        for result in results:
            if isinstance(result, tuple) and len(result) == 2:
                url, content = result
                url_contents[url] = content
            elif isinstance(result, Exception):
                logger.error(f"Error during scraping: {result}")

        if not url_contents:
            raise ValueError("No content could be scraped from the provided URLs.")

        json_file_path = "output.json"
        with open(json_file_path, "w") as json_file:
            json.dump(url_contents, json_file, indent=4)

        background_tasks.add_task(clean_up_file, json_file_path)
        return FileResponse(
            path=json_file_path, filename="output.json", media_type="application/json"
        )
    except Exception as e:
        logger.error(f"Error scraping URLs: {e}")
        raise HTTPException(status_code=500, detail="Failed to scrape URLs. Please try again.")

async def scrape_single_url(url):
    """
    Scrape a single URL's content using aiohttp.
    """
    try:
        logger.info(f"Scraping URL: {url}")
        async with aiohttp.ClientSession(timeout=ClientTimeout(total=TIMEOUT)) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    error_message = f"Failed to scrape {url}, status code: {response.status}"
                    logger.error(error_message)
                    return url, error_message
                content = await response.text()
                logger.info(f"Successfully scraped {url}")
                return url, content
    except ClientError as e:
        error_message = f"Network error scraping {url}: {e}"
        logger.error(error_message)
        return url, error_message
    except asyncio.TimeoutError:
        error_message = f"Timeout error scraping {url}"
        logger.error(error_message)
        return url, error_message
    except Exception as e:
        logger.error(f"Unexpected error scraping {url}: {e}")
        return url, f"Error: {str(e)}"

async def clean_up_file(filepath: str):
    """
    Delete a file after use to clean up resources.
    """
    try:
        os.remove(filepath)
        logger.info(f"Cleaned up file: {filepath}")
    except Exception as e:
        logger.error(f"Error cleaning up file {filepath}: {e}")
