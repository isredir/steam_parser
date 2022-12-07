import scrapy
from urllib.parse import urlencode
from urllib.parse import urljoin
import re
import requests
from bs4 import BeautifulSoup
from scrapy.exceptions import CloseSpider
from spider_steam.items import SpiderSteamItem

queries = ['strategy', 'RPG', 'minecraft']
API = ''


def get_urls():
    start_urls = []
    for q in queries:
        urls = ['https://store.steampowered.com/search/?term=' + str(q) + '&ignore_preferences=1&page=1',
                'https://store.steampowered.com/search/?term=' + str(q) + '&ignore_preferences=1&page=2']
        for url in urls:
            soup = BeautifulSoup(requests.get(url).content.decode("utf-8"), 'html.parser')
            root = soup.find('div', {'id': 'search_resultsRows'})
            games_found = set()
            for i in root.find_all():
                if i.get('href') is not None:
                    game = i.get('href')
                    if game not in games_found:
                        games_found.add(game)
            for game in games_found:
                start_urls.append(game)
    return start_urls


class SteamProductSpider(scrapy.Spider):
    name = 'SteamProductSpider'
    allowed_domains = ['store.steampowered.com']
    start_urls = get_urls()

    def parse(self, response, **kwargs):
        items = SpiderSteamItem()

        name = response.xpath('//div[@id="appHubAppName"][@class="apphub_AppName"]/text()').extract()
        category = response.xpath('//div[@class="blockbg"]/a/text()').extract()
        review_cnt = response.xpath(
            '//div[@itemprop="aggregateRating"]/div[@class="summary column"]/span[@class="responsive_hidden"]/text()').extract()
        total_review = response.xpath(
            '//div[@itemprop="aggregateRating"]/div[@class="summary column"]/span[@class="game_review_summary '
            'positive"]/text()').extract()
        release_date = response.xpath('//div[@class="release_date"]/div[@class="date"]/text()').extract()
        developer = response.xpath('//div[@class="dev_row"]/div[@id="developers_list"]/a/text()').extract()
        tags = response.xpath('//div[@class="glance_tags popular_tags"]/a/text()').extract()
        price = response.xpath('//div[@class="game_purchase_price price"]/text()').extract()
        platforms = response.xpath('//div[@class="sysreq_tabs"]/div/text()').extract()
        
        
        items['game_name'] = ''.join(name).strip()
        items['game_category'] = '/'.join(map(lambda x: x.strip(), category[1:])).strip()
        items['game_review_cnt'] = ''.join(re.sub(r'\D', '', str(review_cnt))).strip()
        items['game_total_review'] = ''.join(total_review).strip()
        items['game_release_date'] = ''.join(release_date).strip()
        items['game_developer'] = ','.join(map(lambda x: x.strip(), developer)).strip()
        items['game_tags'] = ', '.join(map(lambda x: x.strip(), tags)).strip()
        
        try:
            items['game_price'] = ''.join(re.sub(r"[\u0443\u0431\r\t\n]", '',  price[0])).strip()
        except Exception:
            items['game_price'] = ''.join(price).strip()
        
        items['game_platforms'] = ', '.join(map(lambda x: x.strip(), platforms)).strip()
        
        if '\u00ae' in items['game_name']:
        	items['game_name'] = items['game_name'].replace('\u00ae', '')
        if '\u200b' in items['game_name']:
        	items['game_name'] = items['game_name'].replace('\u200b', '')
        if '\u2122' in items['game_name']:
        	items['game_name'] = items['game_name'].replace('\u2122', '')

        if items['game_developer'] != '' and items['game_developer'][0] in '\u0414\u682a':
            items['game_developer'] = ''


        if len(name) != 0 and len(name[0]) != 0 and items['game_release_date'].split()[-1] >= '2000':
            yield items
