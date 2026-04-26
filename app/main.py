import os
import asyncio

from parsers.cyberleninka_parser import CyberleninkaParser as cbp
from parsers.philpapers_parser import PhilpapersParser as ppp
from app.parsers.jmphil_parser import JMPhilParser as jmp
from json_handler import jsonhandler as jh

async def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_root = os.path.dirname(os.path.abspath(__file__))
    links_dir = os.path.join(project_root, "links")
    jsons_dir = os.path.join(app_root, "jsons")
    downloads_dir = os.path.join(project_root, "downloads")

    parsers = [
        cbp(os.path.join(links_dir, "cyberleninka_links.txt")),
        ppp(os.path.join(links_dir, "philpapers_links.txt")),
        jmp(os.path.join(links_dir,"jmphil_links.txt"))
    ]
    json_handlers = [
        jh(os.path.join(jsons_dir, "ssrn.json"), "ssrn"),
        jh(os.path.join(jsons_dir, "jstor.json"), "jstor"),
    ]
    parser_tasks = [
        asyncio.create_task(parser.run(local_path=downloads_dir), name=parser.__class__.__name__)
        for parser in parsers
    ]
    handler_tasks = [
        asyncio.create_task(handler.run(), name=f"{handler.__class__.__name__}:{handler.source}")
        for handler in json_handlers
    ]
    tasks = parser_tasks + handler_tasks
    workers = parsers + json_handlers

    results = await asyncio.gather(*tasks, return_exceptions=True)
    for worker, result in zip(workers, results):
        if isinstance(result, Exception):
            print(f"{worker.__class__.__name__} завершился с ошибкой: {result}")
        else:
            print(f"{worker.__class__.__name__} завершен")

if __name__ == "__main__":
    asyncio.run(main())