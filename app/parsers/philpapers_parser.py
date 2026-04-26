from parsers.abc_parser import *
from bs4 import BeautifulSoup
from requests import get as get_text
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os
import time
from datetime import datetime
from article import ArticleData, ParsedArticle
import re
import asyncio

class PhilpapersParser(ABCParser):
    async def parse(self, url:str) -> ParsedArticle:
        return await asyncio.to_thread(self._parse_sync, url)

    def _parse_sync(self, url:str) -> ParsedArticle:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        
        # Добавляем реалистичные заголовки для обхода блокировки
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': 'Object.defineProperty(navigator, "webdriver", {get: () => false})'
        })
        
        driver.get(url)
        time.sleep(5)  # Увеличиваем задержку для обработки JS
        html_content = driver.page_source

        # Сохраняем HTML в файл для отладки
        self._save_debug_html(html_content, url)

        driver.quit()

        soup = BeautifulSoup(html_content, 'html.parser')
        id = 0

        title = soup.find("h1", itemprop = "name").text.strip()

        abstract = soup.find("div", itemprop = "description").text.strip()

        published_year = 0
        archival_div = soup.find("div", class_="entry-info-partial")
        if archival_div:
            archival_text = archival_div.get_text()
            # Ищем дату в формате YYYY-MM-DD
            date_match = re.search(r'(\d{4})-\d{2}-\d{2}', archival_text)
            if date_match:
                published_year = int(date_match.group(1))

        authors = []
        for author in soup.find_all("span",{"class": "name", "itemprop": "author"}):
            authors.append(author.text.strip())

        keywords = []
        keywords_element = soup.find("div", itemprop = "keywords")
        for keyword in keywords_element.find_all("a"):
            keywords.append(keyword.text.strip())

        views_count = 0
        downloads_count_text = soup.find("span", itemprop = "interactionCount").text.strip()
        downloads_count = int(downloads_count_text.replace(',', ''))

        filename = f"{settings.YADISK_FOLDER}/PhilPapers/{title}.pdf"

        download_url = soup.find("div", {"class" : "pull-right"}).find("a")["href"]
        print(download_url)

        parsed_at = datetime.now().isoformat()

        pdf_content = b""

        article_data = ArticleData(
            id=id,
            title=title,
            source = "PhilPapers",
            abstract=abstract,
            authors=authors,
            keywords=keywords,
            published_year=published_year,
            views_count=views_count,
            downloads_count=downloads_count,
            filename=filename,
            download_url=download_url,
            parsed_at=parsed_at
        )

        return ParsedArticle(
            data=article_data,
            pdf_content=pdf_content
        )

    def _save_debug_html(self, html_content: str, url: str) -> None:
        """Сохраняет HTML контент в файл для отладки"""
        # Создаем папку debug_html если её нет
        debug_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'debug_html')
        os.makedirs(debug_dir, exist_ok=True)
        
        # Генерируем имя файла с таймстемпом
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"philpapers_{timestamp}.html"
        filepath = os.path.join(debug_dir, filename)
        
        # Сохраняем HTML
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"  HTML сохранен: {filepath}")
        print(f"  URL: {url}")