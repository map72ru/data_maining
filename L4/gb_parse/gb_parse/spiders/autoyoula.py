import pymongo
import scrapy
import re
from urllib.parse import unquote
from base64 import b64decode
from json import loads

def get_characteristics(resp):
    values = resp.xpath(
        "//div[@class='AdvertSpecs_row__ljPcX']/div[@class='AdvertSpecs_data__xK2Qx']/text() | ////div[@class='AdvertSpecs_row__ljPcX']/div[@class='AdvertSpecs_data__xK2Qx']/a/text()").extract()
    titles = resp.xpath(
        "//div[@class='AdvertSpecs_row__ljPcX']/div[@class='AdvertSpecs_label__2JHnS']/text()").extract()
    return dict(zip(titles, values))

def get_characteristics_items(elm) -> list:
    items = []
    for itm in elm[1]:
        items.append(dict(zip(itm[1][::2], itm[1][1::2])))
    return items


class AutoyoulaSpider(scrapy.Spider):
    name = "autoyoula"
    allowed_domains = ["auto.youla.ru"]
    start_urls = ["https://auto.youla.ru/"]

    css_query = {
        "brands": "div.TransportMainFilters_brandsList__2tIkv a.blackLink",
        "pagination": "div.Paginator_block__2XAPy a.Paginator_button__u1e7D",
        "ads": "article.SerpSnippet_snippet__3O1t2 a.SerpSnippet_name__3F7Yu",
    }

    data_query = {
        "title": lambda resp: resp.css("div.AdvertCard_advertTitle__1S1Ak::text").get(),
        "price": lambda resp: float(resp.css('div.AdvertCard_price__3dDCr::text').get().replace("\u2009", '')),
        "description": lambda resp: resp.css("div.AdvertCard_descriptionInner__KnuRi::text").get(),
        "main_characteristics": get_characteristics,
    }

    def __init__(self, user, passwd, **kwargs):
        super().__init__(**kwargs)
        self.database = pymongo.MongoClient(f'mongodb+srv://{user}:{passwd}@mdbcluster.cg0fo.mongodb.net/?retryWrites=true&w=majority')[
            'gb_parse_12']

    def parse(self, response, **kwargs):
        brands_links = response.css(self.css_query["brands"])
        yield from self.gen_task(response, brands_links, self.brand_parse)

    def brand_parse(self, response):
        pagination_links = response.css(self.css_query["pagination"])
        yield from self.gen_task(response, pagination_links, self.brand_parse)
        ads_links = response.css(self.css_query["ads"])
        yield from self.gen_task(response, ads_links, self.ads_parse)
#
#   Собрать след стуркутру и сохранить в БД Монго
#   Название объявления
#   Список фото объявления(ссылки)
#   Список характеристик
#   Описание объявления
#   ссылка на автора объявления
#   дополнительно попробуйте вытащить телефона
    def ads_parse(self, response):
        data = {}
        for key, selector in self.data_query.items():
            try:
                data[key] = selector(response)
            except (ValueError, AttributeError):
                continue
        text = response.text
        m = re.search('window.transitState = decodeURIComponent\("(.+?)"\);', text)
        text = unquote(m.group(1))
        m = re.search('"phone","(.+?)"', text)
        # телефон
        if m is not None:
            data['phone'] = "".join([chr(b) for b in b64decode(b64decode(m.group(1)))])
        m = re.search('"youlaId","(.+?)"', text)
        if m is not None:
            data['author_url'] = 'https://youla.ru/user/' + m.group(1)
        # Картинки
        data['images'] = self.get_images(text)
        # Все характеристики
        data['add_characteristics'] = self.get_add_characteristics(text)
        # Сохранение в БД
        collection = self.database['yuola']
        collection.insert_one(data)


    @staticmethod
    def gen_task(response, link_list, callback):
        for link in link_list:
            yield response.follow(link.attrib["href"], callback=callback)

    @staticmethod
    def get_images(text: str) -> list:
        images = []
        data = re.findall('\[\"\^0",\[\"type\",\"photo\",(.+?)]],', text)
        for item in data:
            key = None
            image_set = {}
            for elm in item.split(','):
                if (elm == '"big"' or elm == '"medium"' or elm == '"large"' or elm == '"small"'):
                    key = elm[1:len(elm)-1]
                    continue
                if key is not None:
                    image_set[key] = elm
                    key = None
            images.append(image_set)
        return images

    @staticmethod
    def get_add_characteristics(text) -> dict:
        item = {}
        m = re.search(',"techStruct",\["\^1",(.+?)]]]],"has3d",', text)
        if m is not None:
            text = m.group(1)
            data = loads(text + ']]]')
            for elm in data:
                item[elm[1][1]] = get_characteristics_items(elm[1][3])
        return item

