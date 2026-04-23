from abc import ABC, abstractmethod
import threading
import time
import datetime
from typing import List, Optional
from dataclasses import dataclass
import yadisk
from config import settings
import os
import requests
# Import SQLAlchemy on demand
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, DateTime, cast, ARRAY
import json
import httpx

@dataclass
class ArticleData:
    id: int
    title: str
    source: str
    abstract: str
    author: List[str]
    keywods: List[str]
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

class ABCParser(ABC):
    @abstractmethod
    def parse(self, url: str) -> ParsedArticle:
        raise NotImplementedError("Subclasses must implement this method")
    
    def save(self, article: ParsedArticle, local_path:str):
        # Save metadata to postgres, download pdf to local_path, then upload to yadisk
            token = settings.YADISK_TOKEN

            # Ensure local directory exists
            os.makedirs(local_path, exist_ok=True)

            download_url = getattr(article.data, 'download_url', None)
            
            if not download_url:
                print("Нет download_url в статье — пропускаю скачивание.")
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

                    print(f'Файл скачан локально: {local_file_path}')

                # Upload to Yandex.Disk
                y = yadisk.YaDisk(token=token)
                if not y.check_token():
                    print("Токен Яндекс.Диска недействителен.")
                    return
                dest_file_path =  getattr(article.data, 'filename', 'unknown_file')
                # Если файл уже есть на Яндекс.Диске — пропускаем статью
                try:
                    if y.exists(dest_file_path):
                        print(f'Файл уже существует на Яндекс.Диске: {dest_file_path} — пропускаю статью.')
                        return
                except Exception as e:
                    # Если проверка наличия не удалась, попробуем загрузить и обработаем конфликт ниже
                    print(f'Не удалось проверить существование файла на Диске: {e}')

                try:
                    y.upload(local_file_path, dest_file_path)
                except yadisk.exceptions.PathExistsError:
                    print(f'Файл уже существует на Яндекс.Диске: {dest_file_path} — пропускаю статью.')
                    return
                except yadisk.exceptions.ConflictError:
                    print(f'Конфликт при загрузке (возможно, файл существует): {dest_file_path} — пропускаю статью.')
                    return

                print(f'Файл {local_file_path} загружен на Диск в {dest_file_path}')

                try:
                    
                    authors = getattr(article.data, 'author', []) or []
                    keywords = getattr(article.data, 'keywods', []) or []

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

                    print('Метаданные статьи отправлены на сервер.')

                except httpx.HTTPStatusError as e:
                    print(
                        f"Ошибка при отправке статьи: "
                        f"{e.response.status_code} — {e.response.text}"
                    )

                except Exception as e:
                    print(f"Неожиданная ошибка при отправке статьи: {e}")

            except Exception as e:
                print(f"Ошибка при скачивании/загрузке файла: {e}")
                return