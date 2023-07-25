import hashlib
import json
import os
import scrapy

# import the newspaper parser
from newspaper import Article

# build the scrapy object
class scrapySiteToDisk(scrapy.Spider):

    # configure the crawl
    name = 'site_so_disk'
    allowed_domains = ['www.apache.org', 'apache.org', 'solr.apache.org', 'nutch.apache.org']
    start_urls = ['https://www.apache.org/']

    # parse the fetched html document
    def parse(self, response):
        for title in response.css('head title::text').getall():
            yield {'title': title.strip(), 'url': response.url}

            # Save the raw HTML content to a text file
            md5_hash = hashlib.md5(response.url.encode('utf-8')).hexdigest()
            html_file_name = f"{md5_hash}.html"
            html_folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "html")
            os.makedirs(html_folder_path, exist_ok=True)
            html_file_path = os.path.join(html_folder_path, html_file_name)
            with open(html_file_path, 'w', encoding='utf-8') as f:
                f.write(response.text)

            # Parse the HTML using Newspaper3k and save the JSON result to another file
            article = Article(response.url)
            article.set_html(response.text)
            article.parse()

            # get the word count of the main body text
            word_count = len(article.text.split())

            # only save the file if the body has text
            if word_count > 0:

                # build the array
                parsed_data = {
                    '_id': md5_hash,
                    'id': md5_hash,
                    'title': article.title,
                    'authors': article.authors,
                    'publish_date': article.publish_date.isoformat() if article.publish_date else None,
                    'text': article.text,
                    'word_count': word_count,
                    'top_image': article.top_image,
                    'images': list(article.images),
                    'videos': list(article.movies),
                    'keywords': list(article.keywords),
                    'summary': article.summary
                }

                # store the data
                json_file_name = f"{md5_hash}.json"
                json_folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "json")
                os.makedirs(json_folder_path, exist_ok=True)
                json_file_path = os.path.join(json_folder_path, json_file_name)
                with open(json_file_path, 'w', encoding='utf-8') as f:
                    json.dump(parsed_data, f, ensure_ascii=False, indent=2)

        # recursively get the next page from the que
        for next_page in response.css('a::attr(href)').getall():

            # weed out the images
            if next_page is not None and not self.is_image_url(next_page):

                # crawl the next page
                yield response.follow(next_page, self.parse)

    # weed out image files and other unwanted extensions
    @staticmethod
    def is_image_url(url):
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        return any(url.lower().endswith(ext) for ext in image_extensions)