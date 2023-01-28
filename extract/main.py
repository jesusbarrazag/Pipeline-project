import argparse
import logging
import csv
import datetime

logging.basicConfig(level=logging.INFO)
import re

from requests.exceptions import HTTPError

from urllib3.exceptions import MaxRetryError

import news_page_objects as news
from common import config

is_well_formed_url= re.compile(r'^https?://.+/.+$') # i.e. https://www.somesite.com/something
is_root_path = re.compile(r'^/.+$') # i.e. /some-text
logger = logging.getLogger(__name__)


def _news_scraper(news_site_uid):
    host = config()['news_sites'][news_site_uid]['url']

    logging.info('Iniciando el scrapeado para {}'.format(host))
    logging.info('Encontrando links en homepage...')

    homepage = news.HomePage(news_site_uid, host)

    articles = []

    for link in homepage.article_links:
        article = _fetch_article(news_site_uid, host, link)

        if article:
            logger.info('Articulo obtenido!')
            articles.append(article)

        _save_articles(news_site_uid, articles)


def _fetch_article(news_site_uid, host, link):
    logger.info('Empezar a buscar articulo en  {}'.format(link))

    article = None
    try:
        article = news.ArticlePage(news_site_uid, _build_link(host, link))
    except (HTTPError, MaxRetryError) as e:
        logger.warning('Error al obtener el articulo!', exc_info=False)

    if article and not article.body:
        logger.warning('Articulo invalido. No hay body en la estructura.')
        return None

    return article


def _build_link(host, link):
    if is_well_formed_url.match(link):
        return link
    elif is_root_path.match(link):
        return'{}{}'.format(host, link)
    else:
        return'{host}/{url}'.format(host=host, url=link)


def _save_articles(news_site_uid, articles):
    now = datetime.datetime.now()
    csv_headers = list(filter(lambda property: not property.startswith('_'), dir(articles[0])))
    out_file_name = '{news_site_uid}_{datetime}_articles.csv'.format(news_site_uid=news_site_uid, datetime=now.strftime('%Y_%m_%d'))

    with open(out_file_name, mode = 'w+', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(csv_headers)
        for article in articles:
            row = [str(getattr(article, prop)) for prop in csv_headers]
            writer.writerow(row)

       

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    news_site_choices = list(config()['news_sites'].keys())
    parser.add_argument('news_site',
                        help='The news site that you want to scrape',
                        type=str,
                        choices=news_site_choices)

    args = parser.parse_args()
    _news_scraper(args.news_site)