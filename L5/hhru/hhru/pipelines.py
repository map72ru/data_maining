# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from urllib.parse import urlparse

from itemadapter import ItemAdapter
from pymongo import MongoClient

from L5.hhru.hhru.items import HhruItem


class HhruPipeline(object):

    def __init__(self):
        pass
#        client = MongoClient('localhost', 27017)
#        self.mongobase = client.vacansy_280

    def process_item(self, item, spider):
 #       collection = self.mongobase[spider.name]
 #       collection.insert_one(item)
        print("save: ", item)
        return item

class VacanciesPipeline(object):

    __vacancies = {}

    def process_item(self, item, spider):
        if item.__class__.__name__ == 'HhruItem':
            id = self.__get_employee_id(item['author_url'])
            if id not in self.__vacancies:
                self.__vacancies[id] = []
            self.__vacancies[id].append(item)
        return item

    def __get_employee_id(self, url):
        parsed_url = urlparse(url)
        return parsed_url.path.replace('/employer/', '')
