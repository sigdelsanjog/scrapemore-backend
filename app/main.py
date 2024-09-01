# main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from app.config.models import URLRequest, URLResponse
from app.scraper import fetch_links, write_links_to_csv, extract_unique_categories, extract_unique_pages, extract_unique_tags
import logging
import os

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

async def clean_up_file(filepath: str):
    os.remove(filepath)
