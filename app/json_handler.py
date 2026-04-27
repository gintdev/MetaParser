import argparse
import json
import os
import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from article import ArticleData, ParsedArticle
from config import settings
import httpx
from datetime import datetime
from logging_setup import get_component_logger

class jsonhandler:
    json_path: str
    source: str
    timeout: float
    def __init__(
        self,
        json_path: str,
        source: str,
        timeout: float = 10.0
    ):
        self.json_path = Path(json_path)
        self.source = source
        self.timeout = timeout
        self.logger = get_component_logger(
            f"json_handler.{self.source}",
            f"logs/json_handlers/{self.source}.log"
        )
        
    async def run(self):
        articles = await self.read_articles()
        for article in articles:
            try:
                await self.send_article(article)
            except Exception as e:
                continue

    async def read_articles(self) -> List[ParsedArticle]:
        self.logger.info(f"Начинаю чтение статей из JSON-файла источника {self.source}.")
        try:
            with open(self.json_path, 'r', encoding = 'utf-8') as f:
                data = json.load(f)
                articles = []
                for item in data:
                    title = item.get('title', '')
                    article_data = ArticleData (
                        id = 0,
                        title = title,
                        source = self.source,
                        abstract = item.get('abstract', ''),
                        authors = item.get('authors', []),
                        keywords = item.get('keywords', []),
                        published_year = item.get('published_year', 0),
                        views_count = item.get('views_count', 0),
                        downloads_count = item.get('downloads_count', 0),
                        filename = f"{settings.YADISK_FOLDER}/{self.source}/{title}.pdf",
                        download_url = item.get('download_url', ''),
                        parsed_at = datetime.now().isoformat()
                    )
                    articles.append(ParsedArticle(data=article_data, pdf_content=b""))
                return articles
        except Exception as e:
            self.logger.error(f"Ошибка при чтении JSON-файла {self.json_path}: {e}")
            return []
        
    async def send_article(self, article: ParsedArticle):      
        authors = getattr(article.data, 'author', []) or []
        keywords = getattr(article.data, 'keywords', []) or []

        insert_values = {
            'title': getattr(article.data, 'title', None),
            'source': getattr(article.data, 'source', None),
            'abstract': getattr(article.data, 'abstract', None),
            'authors': authors,
            'keywords': keywords,
            'published_year': getattr(article.data, 'published_year', None),
            'views_count': getattr(article.data, 'views_count', 0),
            'downloads_count': getattr(article.data, 'downloads_count', 0),
            'file_name': getattr(article.data, 'filename', 'unknown_file'),
            'download_url': getattr(article.data, 'download_url', None),
            'parsed_at': getattr(article.data, 'parsed_at', None),
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(settings.API_URL, json=insert_values)
                response.raise_for_status()
            self.logger.info(f'Метаданные статьи {insert_values["title"]} отправлены на сервер.')

        except httpx.HTTPStatusError as e:
            self.logger.error(
                f"Ошибка при отправке статьи {insert_values['title']}: "
                f"{e.response.status_code} — {e.response.text}"
            )

        except Exception as e:
            self.logger.error(f"Ошибка при отправке статьи {insert_values['title']}: {e}")