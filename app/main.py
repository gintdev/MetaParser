from parsers.cyberleninka_parser import CyberleninkaParser as cbp
from parsers.philpapers_parser import PhilpapersParser as ppp
import os

def main():
    links_file = "philpapers_links.txt"
    
    # Проверяем наличие файла
    if not os.path.exists(links_file):
        print(f"Файл {links_file} не найден!")
        return
    
    # Читаем ссылки из файла
    with open(links_file, 'r', encoding='utf-8') as f:
        links = [line.strip() for line in f if line.strip()]
    
    if not links:
        print("Файл пуст или не содержит ссылок!")
        return
    
    parser = ppp()
    
    # Парсим каждую ссылку
    for i, link in enumerate(links, 1):
        try:
            print(f"[{i}/{len(links)}] Парсинг: {link}")
            article = parser.parse(link)
            parser.save(article, local_path="./downloads")
            print(f"✓ Успешно обработана")
        except Exception as e:
            print(f"✗ Ошибка при обработке: {e}")

if __name__ == "__main__":
    main()