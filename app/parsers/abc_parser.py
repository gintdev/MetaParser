from abc import ABC, abstractmethod
import asyncio
from dataclasses import dataclass
import yadisk
from config import settings
from article import ArticleData, ParsedArticle
import os
import requests
# Import SQLAlchemy on demand
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, DateTime, cast, ARRAY
import json
import httpx
from loguru import logger

class ABCParser(ABC):
    links_path: str
    logger
    def __init__(self, links_path: str,logger_path:str):
        self.links_path = links_path
        logger.add(logger_path, level = "INFO")
        self.logger = logger

    async def run(self, local_path: str = "./downloads"):
        if not os.path.exists(self.links_path):
            logger.error(f"Файл {self.links_path} не найден!")
            return
        
        with open(self.links_path, 'r', encoding='utf-8') as f:
            links = [line.strip() for line in f if line.strip()]
            for link in links:
                try:
                    article = await self.parse(link)
                    await self.save(article, local_path)
                except Exception as e:
                    continue

    @abstractmethod
    async def parse(self, url: str) -> ParsedArticle:
        raise NotImplementedError("Subclasses must implement this method")
    
    async def save(self, article: ParsedArticle, local_path:str):
        await asyncio.to_thread(self._save_sync, article, local_path)

    def _save_sync(self, article: ParsedArticle, local_path:str):
        # Save metadata to postgres, download pdf to local_path, then upload to yadisk
            token = settings.YADISK_TOKEN

            # Ensure local directory exists
            os.makedirs(local_path, exist_ok=True)

            download_url = getattr(article.data, 'download_url', None)
            
            if not download_url:
                self.logger.warning(f"Нет download_url в статье {getattr(article.data, 'title', 'unknown_title')} — пропускаю скачивание.")
                return

            try:
                # Stream download to local file
                with requests.get(download_url, stream=True, timeout=60) as resp:
                    resp.raise_for_status()

                    local_file_path = os.path.join(local_path, getattr(article.data, 'title', 'unknown_file') + '.pdf')
                    with open(local_file_path, 'wb') as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)

                # Upload to Yandex.Disk
                y = yadisk.YaDisk(token=token)
                if not y.check_token():
                    self.logger.error("Токен Яндекс.Диска недействителен.")
                    return
                dest_file_path =  getattr(article.data, 'filename', 'unknown_file')
                # Если файл уже есть на Яндекс.Диске — пропускаем статью
                try:
                    if y.exists(dest_file_path):
                        self.logger.info(f'Файл уже существует на Яндекс.Диске: {dest_file_path} — пропускаю статью.')
                        return
                except Exception as e:
                    self.logger.error(f'Не удалось проверить существование файла на Диске: {e}')

                try:
                    y.upload(local_file_path, dest_file_path)
                except yadisk.exceptions.PathExistsError:
                    self.logger.error(f'Файл уже существует на Яндекс.Диске: {dest_file_path} — пропускаю статью.')
                    return
                except yadisk.exceptions.ConflictError:
                    self.logger.error(f'Конфликт при загрузке (возможно, файл существует): {dest_file_path} — пропускаю статью.')
                    return

                self.logger.info(f'Статья {getattr(article.data, "title", "unknown_title")} загружена на Диск по пути {dest_file_path}.')

                try:
                    
                    authors = getattr(article.data, 'authors', []) or []
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

                    with httpx.Client(timeout=10.0) as client:
                        response = client.post(settings.API_URL, json=insert_values)
                        response.raise_for_status()

                    self.logger.info(f'Метаданные статьи {getattr(article.data, "title", "unknown_title")} отправлены на сервер.')

                except httpx.HTTPStatusError as e:
                    self.logger.error(
                        f"Ошибка при отправке статьи: "
                        f"{e.response.status_code} — {e.response.text}"
                    )

                except Exception as e:
                    self.logger.error(f"Неожиданная ошибка при отправке статьи: {e}")

            except Exception as e:
                self.logger.error(f"Ошибка при обработке статьи: {e}")
                return