from pathlib import Path

import requests
import time
import json

class StatusCodeError(Exception):
    def __init__(self, txt):
        self.txt = txt

class Parser5ka:
    headers = {
        'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.16; rv:84.0) Gecko/20100101 Firefox/84.0"
    }

    __offers_url = '/special_offers'
    __categories_url = '/categories'
    __debug_mode = False

    def __init__(self, start_url, __debug_mode = False):
        self.__start_url = start_url
        self.__debug_mode = __debug_mode

    def __get_response(self, url: str,  **kwargs):
        while True:
            try:
                response = requests.get(url, **kwargs)
                if response.status_code != 200:
                    raise StatusCodeError(f'status {response.status_code}')
                return response
            except (requests.exceptions.ConnectTimeout, StatusCodeError):
                self.__log('Restart request')
                time.sleep(0.1)

    def __get_categories(self):
        url = self.__start_url + self.__categories_url
        response = self.__get_response(url)
        return response.json()

    def __log(self, message):
        if self.__debug_mode:
            print(message)

    def run(self):
        categories = self.__get_categories()
        for cat in categories:
            self.__log(f"Read category: {cat['parent_group_name']}")
            cat['products'] = []
            for products in self.__parse(self.__start_url + self.__offers_url, cat['parent_group_code']):
                for product in products:
                    self.__log(f"Add product: {product['name']}")
                    cat['products'].append(product)
            file_path = Path(__file__).parent.joinpath(f'{cat["parent_group_code"]}.json')
            self.__save_file(file_path, cat)

    def __parse(self, url, categoryCode):
        while url:
            response = self.__get_response(self, headers=self.headers, params={'categories': categoryCode})
            data: dict = response.json()
            url = data['next']
            yield data.get('results', [])

    def __save_file(self, file_path: Path, data):
        self.__log(f"Save file: {file_path}")
        with open(file_path, 'w', encoding='UTF-8') as file:
            json.dump(data, file, ensure_ascii=False)
