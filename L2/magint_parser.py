from datetime import datetime
import re

import requests
import bs4
from urllib.parse import urljoin
import pymongo


class MagnitParse:
    __months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
    __count = 0

    def __init__(self, start_url, mongo_db):
        self.start_url = start_url
        self.db = mongo_db

    def __get_soup(self, url) -> bs4.BeautifulSoup:
        # todo предусмотреть внештатные ситуации
        response = requests.get(url)
        return bs4.BeautifulSoup(response.text, 'lxml')

    def run(self):
        _count = 0
        for product in self.parse():
            self.save(product)

    def parse(self):
        soup = self.__get_soup(self.start_url)
        catalog_main = soup.find('div', attrs={'class': 'сatalogue__main'})
        for product_tag in catalog_main.find_all('a', recursive=False):
            if not 'card-sale_banner' in product_tag.attrs['class']:
                yield self.product_parse(product_tag)

    def __make_dates(self, text: str) -> [datetime, datetime]:
        tokens = text.splitlines()
        tokens.remove('')
        if len(tokens) > 2 or len(tokens) == 0:
            raise Exception('Invalid convert str to date: ' + text)

        m = re.search(r'^\s*(с|Только)\s+(\d{1,2})\s+(\w+)\s*$', tokens[0], flags=re.U)

        if m is None or len(m.groups()) != 3:
            raise Exception('Invalid date parser (group count): ' + tokens[0])

        day = int(m.group(2))
        month = self.__months.index(m.group(3))
        year = datetime.today().year

        from_date = datetime(year, month+1, day)

        if m.group(1) != 'Только':
            m = re.search(r'^\s*до\s+(\d{1,2})\s+(\w+)\s*$', tokens[1])

            if m is None or len(m.groups()) != 2:
                raise Exception('Invalid date parser (group count): ' + tokens[1])

            day = int(m.group(1))
            to_month = self.__months.index(m.group(2))
            year = datetime.today().year
            if to_month < month and month == 11:
                year = year + 1

            to_date = datetime(year, to_month+1, day)
        else:
            to_date = None

        return [from_date, to_date]

    def __make_price(self, text) -> float:
        tokens = text.splitlines()
        tokens.remove('')
        if len(tokens) != 2:
            print('Invalid convert str to float: ' + text)
            return 0

        return float(f'{tokens[0]}.{tokens[1]}')

###
#    пример структуры и типы обязательно хранить поля даты как объекты datetime
#    {
#        "url": str,
#        "promo_name": str,
#        "product_name": str,
#        "old_price": float,
#        "new_price": float,
#        "image_url": str,
#        "date_from": "DATETIME",
#        "date_to": "DATETIME",
#    }
###

    def product_parse(self, product: bs4.Tag) -> dict:
        dates = self.__make_dates(product.find('div', attrs={'class': 'card-sale__date'}).text)
        old_price = product.find('div', attrs={'class': 'label__price_old'})
        new_price = product.find('div', attrs={'class': 'label__price_new'})
        promo = product.find('div', attrs={'class': 'card-sale__name'})

        data = {
            'url': urljoin(self.start_url, product.get('href')),
            'promo_name': promo.text if not promo is None else None,
            'product_name': product.find('div', attrs={'class': 'card-sale__title'}).text,
            'old_price': self.__make_price(old_price.text) if not old_price is None else 0,
            'new_price': self.__make_price(new_price.text) if not new_price is None else 0,
            'image_url': urljoin(self.start_url, product.find('img').attrs['data-src']),
            'date_from': dates[0],
            'date_to' : dates[1]
        }
        return data

    def save(self, data):
        collection = self.db['magnit']
        collection.insert_one(data)
        print(self.__count)
        self.__count = self.__count + 1


if __name__ == '__main__':
    database = pymongo.MongoClient('mongodb+srv://test:Ghjcnj1@mdbcluster.cg0fo.mongodb.net/?retryWrites=true&w=majority')['gb_parse_12']
    result = database.db['magnit'].delete_many({})
    print(f'Delete documents: {result.deleted_count}')
    parser = MagnitParse("https://magnit.ru/promo/?geo=moskva", database)
    parser.run()