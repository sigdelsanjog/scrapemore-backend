from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from urllib.parse import urlparse
import logging
import os
from app.config.models import URLRequest, URLResponse, URLListRequest, ContentResponse
from app.engine.scraper import fetch_links, scrape_content,write_links_to_csv, extract_unique_categories, extract_unique_pages, extract_unique_tags

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
        # Fetch all unique links from the given URL
        all_links = await fetch_links(request.url)

        # Categorize the links into Pages, Tags, and Categories
        pages = [link['link'] for link in extract_unique_pages(all_links)]
        tags = [link['link'] for link in extract_unique_tags(all_links)]
        categories = [link['link'] for link in extract_unique_categories(all_links)]

        # Log each URL category as it is processed
        logger.info(f"Pages: {pages}")
        logger.info(f"Tags: {tags}")
        logger.info(f"Categories: {categories}")
        
        # Prepare the response structure
        response = [
            {"category": "Pages", "urls": pages},
            {"category": "Tags", "urls": tags},
            {"category": "Categories", "urls": categories},
        ]

        return {"urls": response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scrape-links/")
async def scrape_links(url: str, background_tasks: BackgroundTasks):
    links = await fetch_links(url)
    
    # Write the links to a CSV file
    csv_file_path = await write_links_to_csv(links)

    # Return the CSV file as a downloadable response
    background_tasks.add_task(clean_up_file, csv_file_path)
    return FileResponse(path=csv_file_path, filename="unique_links.csv", media_type="text/csv")

async def clean_up_file(filepath: str):
    """Delete the file after sending the response."""
    os.remove(filepath)