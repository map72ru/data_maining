# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class HhruItem(scrapy.Item):
    _id = scrapy.Field()
    name = scrapy.Field()
    salary = scrapy.Field()
    skills = scrapy.Field()
    description = scrapy.Field()
    author_url = scrapy.Field()


class AuthorItem(scrapy.Item):
    _id = scrapy.Field()
    name = scrapy.Field()
    site = scrapy.Field()
    spheres = scrapy.Field()
    vacancies = scrapy.Field()
