"""Scrapy spider that crawls a site and stores every page to disk.

Each crawled page is saved twice: the raw HTML under html/ and a
structured JSON document (parsed with Newspaper3k) under json/. The JSON
documents are shaped for direct ingestion into a search engine such as
Solr, OpenSearch, or Elasticsearch.
"""

import hashlib
import json
import os

import scrapy
from newspaper import Article

IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')


class ScrapySiteToDisk(scrapy.Spider):
    name = 'site_to_disk'

    # Defaults; override at the command line with -a, for example:
    # scrapy runspider myspider.py -a start_url=https://example.com -a allowed=example.com,www.example.com
    def __init__(self, start_url='https://www.apache.org/', allowed=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [start_url]
        if allowed:
            self.allowed_domains = [d.strip() for d in allowed.split(',')]
        else:
            self.allowed_domains = [
                'www.apache.org',
                'apache.org',
                'solr.apache.org',
                'nutch.apache.org',
            ]
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.html_dir = os.path.join(base_dir, 'html')
        self.json_dir = os.path.join(base_dir, 'json')
        os.makedirs(self.html_dir, exist_ok=True)
        os.makedirs(self.json_dir, exist_ok=True)

    def parse(self, response):
        # A stable document id derived from the URL keeps re-crawls idempotent.
        doc_id = hashlib.md5(response.url.encode('utf-8')).hexdigest()
        title = (response.css('head title::text').get() or '').strip()
        yield {'title': title, 'url': response.url}

        # Save the raw HTML.
        html_path = os.path.join(self.html_dir, f'{doc_id}.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(response.text)

        # Parse the page with Newspaper3k and save the structured result.
        article = Article(response.url)
        article.set_html(response.text)
        article.parse()

        word_count = len(article.text.split())
        if word_count > 0:
            parsed_data = {
                '_id': doc_id,
                'id': doc_id,
                'title': article.title,
                'authors': article.authors,
                'publish_date': article.publish_date.isoformat() if article.publish_date else None,
                'text': article.text,
                'word_count': word_count,
                'top_image': article.top_image,
                'images': list(article.images),
                'videos': list(article.movies),
                'keywords': list(article.keywords),
                'summary': article.summary,
                'url': response.url,
            }
            json_path = os.path.join(self.json_dir, f'{doc_id}.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(parsed_data, f, ensure_ascii=False, indent=2)

        # Follow links, skipping direct links to image files.
        for next_page in response.css('a::attr(href)').getall():
            if next_page and not next_page.lower().endswith(IMAGE_EXTENSIONS):
                yield response.follow(next_page, self.parse)
