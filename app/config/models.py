from pydantic import BaseModel
from typing import List, Dict

class URLRequest(BaseModel):
    url: str

class URLCategory(BaseModel):
    category: str
    urls: list[str]

class URLResponse(BaseModel):
    urls: list[URLCategory]

class URLListRequest(BaseModel):
    urls: list[str]

class ContentResponse(BaseModel):
    contents: dict