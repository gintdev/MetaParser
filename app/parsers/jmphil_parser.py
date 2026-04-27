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
import random

class JMPhilParser(ABCParser):
    async def parse(self, url:str) -> ParsedArticle:
        try:
            return await asyncio.to_thread(self._parse_sync, url)
        except Exception as e:
            self.logger.error(f"Ошибка при парсинге статьи по ссылке {url}:\n{e}")

    def _parse_sync(self, url: str) -> ParsedArticle:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
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
        time.sleep(random.uniform(7,11))
        html_content = driver.page_source

        soup = BeautifulSoup(html_content, 'html.parser')

        title = soup.find("h1").text.strip()

        abstract_element = soup.find("h3", text = "Abstract")
        abstract_element_siblings = abstract_element.find_next_siblings() if abstract_element else []
        abstract = ""
        for sibling in abstract_element_siblings:
            if "Keywords:" in sibling.text.strip():
                break
            if(len(abstract) <  len(sibling.text.strip())):
                abstract = sibling.text.strip()

        author = soup.find("span", itemprop = "name").text.strip()

        keyword_element = soup.find("strong", string=re.compile(r"^\s*Keywords\s*:?\s*$", re.IGNORECASE))
        keywords = []
        if keyword_element and keyword_element.parent:
            keywords_text = keyword_element.parent.get_text(" ", strip=True)
            keywords_text = re.sub(r"^\s*Keywords\s*:?\s*", "", keywords_text, flags=re.IGNORECASE)
            keywords = [kw.strip() for kw in keywords_text.split(",") if kw.strip()]
        
        published_year = 0
        published_element = soup.find("p", id="article_date_published")
        if published_element:
            published_text = published_element.get_text(" ", strip=True)
            date_match = re.search(r"(\d{4})-\d{2}-\d{2}", published_text)
            if date_match:
                published_year = int(date_match.group(1))

        views_count = 0
        download_count = 0
        views_element = None
        download_element = None
        for candidate in soup.find_all("p", class_="number"):
            label = candidate.find("span")
            if label and re.search(r"\bViews\b", label.get_text(" ", strip=True), re.IGNORECASE):
                views_element = candidate
                continue
            if label and re.search(r"\bDownloads\b", label.get_text(" ", strip=True), re.IGNORECASE):
                download_element = candidate
                continue
            if views_element and download_element:
                break

        if views_element:
            views_text = views_element.get_text(" ", strip=True)
            views_text = re.sub(r"\bViews\b", "", views_text, flags=re.IGNORECASE)
            digits = re.sub(r"\D", "", views_text)
            views_count = int(digits) if digits else 0

        if download_element:
            download_text = download_element.get_text(" ", strip=True)
            download_text = re.sub(r"\bDownloads\b", "", download_text, flags=re.IGNORECASE)
            digits = re.sub(r"\D", "", download_text)
            download_count = int(digits) if digits else 0
        
        download_url = "https://jmphil.org" + soup.find("a", text = "Download PDF")["href"]
        parsed_at = datetime.now().isoformat()
        source = "JMPhil"
        filename = f"{settings.YADISK_FOLDER}/{source}/{title}.pdf"
        
        article_data = ArticleData(
            id=0,
            title=title,
            source=source,
            abstract=abstract,
            authors=[author],
            keywords=keywords,
            published_year=published_year,
            views_count=views_count,
            downloads_count=download_count,
            filename=filename,
            download_url=download_url,
            parsed_at=parsed_at
        )

        self.logger.info(f'Статья "{title}" успешно собрана. Источник: {source}.')

        return ParsedArticle(
            data=article_data,
            pdf_content=b""
        )