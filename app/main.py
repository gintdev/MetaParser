from parsers.cyberleninka_parser import CyberleninkaParser as cbp

def main():
    link = "https://cyberleninka.ru/article/n/sostradanie-i-odinochestvo-v-etike-shopengauera"
    parser = cbp()
    article = parser.parse(link)
    parser.save(article, local_path="./downloads")


if __name__ == "__main__":
    main()