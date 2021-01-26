import scrapy
import re
from urllib.parse import unquote
from base64 import b64decode

def get_characteristics(resp):
    values = resp.xpath(
        "//div[@class='AdvertSpecs_row__ljPcX']/div[@class='AdvertSpecs_data__xK2Qx']/text() | ////div[@class='AdvertSpecs_row__ljPcX']/div[@class='AdvertSpecs_data__xK2Qx']/a/text()").extract()
    titles = resp.xpath(
        "//div[@class='AdvertSpecs_row__ljPcX']/div[@class='AdvertSpecs_label__2JHnS']/text()").extract()
    return dict(zip(titles, values))

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
        "characteristics": get_characteristics,
    }

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
        if m is not None:
            phone = b64decode(m.group(1))
            data['phone'] = phone
        m = re.search('"youlaId","(.+?)"', text)
        if m is not None:
            data['author_url'] = 'https://youla.ru/user/' + m.group(1)






    @staticmethod
    def gen_task(response, link_list, callback):
        for link in link_list:
            yield response.follow(link.attrib["href"], callback=callback)