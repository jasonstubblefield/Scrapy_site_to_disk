# Site to Disk

This is a scrapy spider that crawls site(s) and stores them to the disk.

Each html page is parsed and stored as a json file.

The html is stored as a html file.

### Prerequisites

Make sure you have scrapy installed.

Make sure you have Newspaper3k installed.

### Configuration

Change the seed url and allowed hostnames in the runspider.py file.

### Usage

Run the spider ...

`scrapy runspider myspider.py`

### Output

The HTML will be stored in a html folder. 

The JSON will be stored in a json folder

### Questions

if you like this script and/or want to ask questions check out my personal site at https://jasonstubblefield.github.io


