# main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from app.config.models import URLRequest, URLResponse, URLListRequest
from app.scraper import fetch_links, write_links_to_csv, extract_unique_categories, extract_unique_pages, extract_unique_tags
import logging
import os
import json
import asyncio
import aiohttp  # Make sure aiohttp is installed in your environment
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the maximum number of threads for parallel scraping
MAX_THREADS = 5  # Configurable number of threads, adjust as necessary

@app.post("/analyze", response_model=URLResponse)
async def analyze_url(request: URLRequest):
    try:
        visited_links = set()
        all_links = await fetch_links(request.url, visited_links)

        # Categorize the links into Pages, Tags, and Categories
        pages = extract_unique_pages(all_links)
        tags = extract_unique_tags(all_links)
        categories = extract_unique_categories(all_links)

        # Prepare a flat list of URLs for response
        response_urls = []

        # Flatten the categories, pages, and tags into individual URL entries
        for page in pages:
            response_urls.append({"category": "Page", "url": page['link']})

        for tag in tags:
            response_urls.append({"category": tag['category'], "url": tag['link']})

        for category in categories:
            response_urls.append({"category": category['category'], "url": category['link']})

        # Log the prepared response
        logger.info(f"Prepared response: {response_urls}")

        return {"urls": response_urls}

    except Exception as e:
        logger.error(f"Error in /analyze: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scrape-links/")
async def scrape_links(request: URLRequest, background_tasks: BackgroundTasks):
    visited_links = set()
    links = await fetch_links(request.url, visited_links)

    csv_file_path = await write_links_to_csv(links)

    background_tasks.add_task(clean_up_file, csv_file_path)
    return FileResponse(path=csv_file_path, filename="unique_links.csv", media_type="text/csv")


@app.post("/scrape-all-urls/")
async def scrape_url_content(request: URLListRequest):
    """
    Scrape the contents of multiple URLs concurrently and save them into a JSON file.
    """
    try:
        # Use ThreadPoolExecutor for parallel execution
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            results = await asyncio.gather(
                *[loop.run_in_executor(executor, scrape_single_url, url) for url in request.urls]
            )

        # Create a dictionary with URL contents
        url_contents = {url: content for url, content in results}

        # Save the scraped contents into a JSON file
        json_file_path = "output.json"
        with open(json_file_path, "w") as json_file:
            json.dump(url_contents, json_file, indent=4)

        # Return the JSON file as a response
        return FileResponse(path=json_file_path, filename="output.json", media_type="application/json")

    except Exception as e:
        logger.error(f"Error scraping URLs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def scrape_single_url(url):
    """
    Scrape a single URL's content using aiohttp.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                content = await response.text()
                return url, content
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
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

