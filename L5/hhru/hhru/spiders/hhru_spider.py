import scrapy
from scrapy.http import HtmlResponse
from L5.hhru.hhru.items import HhruItem, AuthorItem
from urllib.parse import urlparse, ParseResult, urlunparse


class HhruSpider(scrapy.Spider):
    name = 'hhru_spider'
    allowed_domains = ['hh.ru']
    start_urls = ['https://hh.ru/search/vacancy?schedule=remote&L_profession_id=0&area=113']

    def parse(self, response):
        next_page = response.css('a.HH-Pager-Controls-Next::attr(href)').extract_first()
        yield response.follow(next_page, callback=self.parse)

        vacansy = response.css(
            'div.vacancy-serp div.vacancy-serp-item div.vacancy-serp-item__row_header a.bloko-link::attr(href)'
        ).extract()

        for link in vacansy:
            yield response.follow(link, callback=self.vacansy_parse)

    def vacansy_parse(self, response: HtmlResponse):
        name = response.css('div.vacancy-title h1.bloko-header-1::text').extract_first()
        salary = self.__make_join(response.xpath("//div[@class='vacancy-title']//span/text()").extract())
        description = response.xpath("//div[@class='vacancy-description']//p/text()").extract()
        skills = response.xpath("//div[@class='bloko-tag-list']//span/text()").extract()
        author_url = self.__make_url(response.request.url, response.xpath("//a[@class='vacancy-company-name']/@href").extract_first())
        # print(name, salary)
        yield HhruItem(name=name, salary=salary, description=description, skills=skills, author_url=author_url)

        yield response.follow(author_url, callback=self.author_parse)

    def __make_url(self, url, path):
        parsed_url = urlparse(url)
        return urlunparse(ParseResult(parsed_url.scheme, parsed_url.netloc, path, None, None, None))

    def __make_join(self, sallary: list):
        out_sallary = ' '.join(sallary)
        return out_sallary.replace('\\xa0', ' ').strip()

    def author_parse(self, response: HtmlResponse):
        name = self.__make_join(response.xpath("//div[@class='employer-sidebar-header']//span[@class='company-header-title-name']/text()").extract())
        site = response.xpath("//a[@data-qa='sidebar-company-site']/@href").extract_first()
        spheres = response.xpath("//div[@class='employer-sidebar-block']//p/text()").extract()

        yield AuthorItem(name=name, site=site, spheres =spheres)
