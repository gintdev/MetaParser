# There will be implemented a parser for SSRN in the future
from parsers.abc_parser import *
from bs4 import BeautifulSoup
from requests import get as get_text
from selenium import webdriver


class SSRNParser(ABCParser):
    def parse(self, url: str) -> ParsedArticle:

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

        driver = webdriver.Chrome(options=options)
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': 'Object.defineProperty(navigator, "webdriver", {get: () => false})'
        })
        
        driver.get(url)
        time.sleep(5)  # Увеличиваем задержку для обработки JS
        html_content = driver.page_source

        driver.quit()
        print(html_content)