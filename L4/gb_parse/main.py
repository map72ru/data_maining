from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from L4.gb_parse.gb_parse.spiders.autoyoula import AutoyoulaSpider
import os
from dotenv import load_dotenv

if __name__ == '__main__':
    load_dotenv()
    crawler_settings = Settings()
    crawler_settings.setmodule('gb_parse.settings')
    crawler_process = CrawlerProcess(settings=crawler_settings)
    crawler_process.crawl(AutoyoulaSpider, os.getenv('USER'), os.getenv('PASSWD'))
    crawler_process.start()