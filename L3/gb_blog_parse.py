import os

import requests
import bs4
import datetime
import json
from urllib.parse import urljoin, ParseResult, urlencode
from urllib.parse import urlparse
from urllib.parse import urlunparse
from dotenv import load_dotenv

from database import Database


# todo обойти пагинацию блога
# todo обойти каждую статью
# todo Извлечь данные: Url, Заголовок, имя автора, url автора, список тегов (url, имя)


class GbParse:
    __debug = True

    def __init__(self, start_url, database):
        self.start_url = start_url
        self.database = database

    def __log(self, message):
        if self.__debug:
            print((message))

    def run(self):
        page_no = 1
        while True:
            page = requests.get(self.start_url, params={'page': page_no})
            soup = bs4.BeautifulSoup(page.text, 'lxml')

            self.__log(f'Parse page {page_no}')

            posts_urls = soup.find_all('a', attrs={'class': 'post-item__title'})

            if posts_urls is None or len(posts_urls) == 0:
                break

            for post_url in posts_urls:
                post_href = urljoin(self.start_url, post_url.get('href'))
                result = self.post_parse(post_href)
                if result:
                    self.__log(f"Save to db: {result['post_data']['title']}")
                    self.database.create_post(result)

            page_no = page_no + 1

    ###
    #    Необходимо обойти все записи в блоге и извлеч из них информацию следующих полей:
    #    url страницы материала
    #    Заголовок материала
    #    Первое изображение материала(Ссылка)
    #    Дата публикации(в формате datetime)
    #    имя автора материала
    #    ссылка на страницу автора материала
    #    комментарии в виде(автор комментария и текст комментария)
    #    список тегов
    ###
    def post_parse(self, url) -> dict:
        soup = bs4.BeautifulSoup(requests.get(url).text, 'lxml')
        author_name_tag = soup.find('div', attrs={'itemprop': 'author'})
        data = {
            'post_data': {
                'url': url,
                'title': soup.find('h1', attrs={'class': 'blogpost-title'}).text,
                'published_date': datetime.datetime.strptime(soup.find('time').attrs['datetime'],
                                                             '%Y-%m-%dT%H:%M:%S%z'),
                'picture_url': self.__get_post_picture(soup)
            },
            'author': {
                'url': urljoin(url, author_name_tag.parent.get('href')),
                'name': author_name_tag.text,
            },
            'tags': [{
                'name': tag.text,
                'url': urljoin(url, tag.get('href')),
            } for tag in soup.find_all('a', attrs={'class': 'small'})],
            'comments': self.find_comments(soup.find('comments'))
        }
        return data

    def find_comments(self, tag) -> []:
        out_comments = []
        if tag is not None:
            parsed_url = urlparse(self.start_url)
            comment_url = urlunparse(ParseResult(parsed_url.scheme, parsed_url.netloc, 'api/v2/comments',
                                                 parsed_url.params,
                                                 urlencode({'commentable_id': tag.get('commentable-id'),
                                                            'commentable_type': tag.get('commentable-type')}),
                                                 parsed_url.fragment))
            try:
                comments = json.loads(requests.get(comment_url).text)
                for comment in comments:
                    short_comment = {
                        'author': {'name': comment['comment']['user']['full_name'],
                                   'url': comment['comment']['user']['url']},
                        'text': comment['comment']['body']
                    }
                    out_comments.append(short_comment)
            except Exception as e:
                raise Exception(f"Error on get comment with id={tag.get('commentable-id')} and message {e.__str__()}")

        return out_comments

    @staticmethod
    def __get_post_picture(soup):
        img = soup.find('div', attrs={'class': 'blogpost-content content_text content js-mediator-article'}).find(
            'img')
        if img is not None:
            return img.attrs['src']
        return ''


if __name__ == '__main__':
    load_dotenv('.env')
    parser = GbParse('https://geekbrains.ru/posts',
                     Database(os.getenv('SQL_DB')))
    parser.run()
