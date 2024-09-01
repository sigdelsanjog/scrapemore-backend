from pydantic import BaseModel
from typing import List, Dict

class URLRequest(BaseModel):
    url: str

class URLItem(BaseModel):
    category: str
    url: str

class URLResponse(BaseModel):
    urls: list[URLItem]

class URLListRequest(BaseModel):
    urls: list[str]

class ContentResponse(BaseModel):
    contents: dict