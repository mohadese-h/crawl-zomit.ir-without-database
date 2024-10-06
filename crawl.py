from abc import ABC, abstractmethod
from config import LINK, CATEGORIES, DATA
import requests
from bs4 import BeautifulSoup
import json


class CrawlBase(ABC):
    @abstractmethod
    def start(self):
        pass

    @staticmethod
    def get(link):
        try:
            response = requests.get(link)
        except requests.HTTPError:
            return None
        return response

    @abstractmethod
    def store(self, data):
        pass


class CrawlerLink(CrawlBase):
    def __init__(self, url=LINK, category=CATEGORIES):
        self.url = url
        self.category = category

    @staticmethod
    def find_link(html_doc):
        soup = BeautifulSoup(html_doc, 'html.parser')
        link = soup.find_all('a',
                             'link__CustomNextLink-sc-1r7l32j-0 eoKbWT ProductListItemDesktop__OverlayLink-sc-1cfkp5x-5 euacZy')
        https_link = [l.get('href') for l in link]
        return set(https_link)


    def crawl_start_category(self,link, category):
         list_link = []
         for c in category:
            response = self.get(link + c)
            if response is None:
                 print("response is None")
                 continue
            new_link = self.find_link(response.text)
            list_link.extend(new_link)
            print(f'{c}, total :{len(new_link)}')
         return list_link

    def start(self, store=True):
        links = []
        for c in self.category.keys():
            print(f'{c} :')
            link = self.crawl_start_category(self.url.format(c) , self.category[c])
            links.extend(link)
            if store:
                i = 0
                for l in link:
                    self.store(l, i, c)
                    i += 1
        return links

    def store(self, data, *args):
        with open(f'links/{args[1]}/{args[0]}.json', 'w') as f:
            f.write(json.dumps(data))


class CrawlerData(CrawlBase):
    def __init__(self):
        self.links = []


    @staticmethod
    def load_links(category):
        i = 0
        links = []
        try:
            while True:
                with open(f'links/{category}/{i}.json', 'r') as f:
                    link = json.loads(f.read())
                    links.append(link)
                    i += 1
        except FileNotFoundError:
            return links

    def start(self):
        for c in CATEGORIES.keys():
            links = self.load_links(c)
            for link in links:
                data = self.find_data(link)
                self.store(data, c)

    def find_data(self, link):
        data = DATA
        response = self.get(link)
        if response is not None:
            soup = BeautifulSoup(response.text, 'html.parser')
            name = soup.find('h2', 'sc-63f15cb9-0 jlSfXh')
            data['name'] = name.text

            rate = soup.find('span', 'sc-63f15cb9-0 CaNjV rate-value fa')
            data['rate'] = rate.text

            price_min = soup.find('span', 'sc-63f15cb9-0 fgYdgD fa')
            if price_min:
                price_max = soup.find('span', 'sc-63f15cb9-0 kmTBcX fa')
                data['price']['min'] = price_min.text
                data['price']['max'] = price_max.text

            specification = soup.find_all('span', 'sc-63f15cb9-0 jyHoEX sc-310e018-1 kVvfyQ')
            specifications = []
            for i in specification:
                if i.text != '_':
                    specifications.append(i.text)

            data['specifications'] = specifications
            return data
        else:
            print("response is None")
            return

    def store(self, data, *args):
        with open(f'data/{args[0]}/{data['name']}.json', 'w') as f:
            f.write(json.dumps(data,ensure_ascii=False))
