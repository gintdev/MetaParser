import threading
import time
import datetime
from dataclasses import dataclass
from typing import List

@dataclass
class ArticleData:
    id: int
    title: str
    source: str
    abstract: str
    authors: List[str]
    keywords: List[str]
    published_year: int
    views_count: int
    downloads_count:int
    filename: str
    download_url: str
    parsed_at: datetime.datetime

@dataclass 
class ParsedArticle:
    data: ArticleData
    pdf_content: bytes