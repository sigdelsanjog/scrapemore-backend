from pydantic import BaseModel
from typing import List, Dict

class UrlResponse(BaseModel):
    urls: List[str]
    categories: list[str]  # Add categories to this response model

class ContentResponse(BaseModel):
    contents: Dict[str, Dict[str, str]]

# Rename or create CategoryResponse for clarity
class CategoryResponse(BaseModel):
    urls: list[str]
    categories: list[str]