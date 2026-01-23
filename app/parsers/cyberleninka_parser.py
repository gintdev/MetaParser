from parsers.abc_parser import *
from bs4 import BeautifulSoup
from requests import get as get_text
from selenium import webdriver

class CyberleninkaParser(ABCParser):
    def parse(self, url:str) -> ParsedArticle:

        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')

        driver = webdriver.Chrome(options=options)
        driver.get(url)
        time.sleep(3)
        html_content = driver.page_source
        driver.quit()

        soup = BeautifulSoup(html_content, 'html.parser')
        
        id = 0

        published_year = soup.find("time", itemprop="datePublished").text.strip()

        title_element = soup.find("i", {"itemprop": "headline"})
        title = title_element.text if title_element else ""
        
        # Извлечение списка авторов
        authors = []

        author_list = soup.find("ul", class_="author-list")
        if author_list:
            for li in author_list.find_all("li", itemprop="author"):
                span = li.find("span")
                if span:
                    authors.append(span.get_text(strip=True))

        keywords = []
        keywords_list = soup.find("i", itemprop="keywords").find_all("span")
        for keyword in keywords_list:
            keywords.append(keyword.text.strip())
        # Извлечение количества просмотров
        views_element = soup.find("div", {"class": "statitem views"})
        views_count = 0
        if views_element:
            views_text = views_element.get_text()
            views_count = int(''.join(filter(str.isdigit, views_text))) if any(c.isdigit() for c in views_text) else 0
        
        # Извлечение количества загрузок
        downloads_element = soup.find("div", {"class": "statitem downloads"})
        downloads_count = 0
        if downloads_element:
            downloads_text = downloads_element.get_text()
            downloads_count = int(''.join(filter(str.isdigit, downloads_text))) if any(c.isdigit() for c in downloads_text) else 0

        abstract = soup.find("p", {"itemprop": "description"}).text.strip() if soup.find("p", {"itemprop": "description"}) else ""
        
        filename = "" # Как на яндекс дсике

        download_url = "https://cyberleninka.ru/article/n/" + soup.find("a", title = 'Скачать')["href"]

        parsed_at = datetime.datetime.now().isoformat()

        pdf_content = b""

        article_data = ArticleData(
            id=id,
            title=title,
            source = "Cyberleninka",
            abstract=abstract,
            author=authors,
            keywods=keywords,
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