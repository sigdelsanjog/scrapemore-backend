from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.scraper import fetch_links, scrape_content, extract_unique_categories
from app.schemas import UrlResponse, ContentResponse

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # Adjust as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class URLRequest(BaseModel):
    url: str

@app.post("/analyze", response_model=UrlResponse)
async def analyze_url(request: URLRequest):
    try:
        urls = await fetch_links(request.url)
        categories = extract_unique_categories(urls)
        return {"urls": urls, "categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class URLListRequest(BaseModel):
    urls: list[str]

@app.post("/scrape", response_model=ContentResponse)
async def scrape_urls(request: URLListRequest):
    try:
        contents = await scrape_content(request.urls)
        return {"contents": contents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
