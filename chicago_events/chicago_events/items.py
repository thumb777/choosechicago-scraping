# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ChicagoEventItem(scrapy.Item):
    event_id = scrapy.Field()
    name = scrapy.Field()
    description = scrapy.Field()
    url = scrapy.Field()
    status = scrapy.Field()
    start_date = scrapy.Field()
    start_time = scrapy.Field()
    venue_name = scrapy.Field()
    venue_address = scrapy.Field()
    venue_city = scrapy.Field()
    venue_state = scrapy.Field()
    venue_country = scrapy.Field()
    venue_location_latitude = scrapy.Field()
    venue_location_longitude = scrapy.Field()
    price_min = scrapy.Field()
    price_max = scrapy.Field()
    image_url = scrapy.Field()
    categories = scrapy.Field()
    source = scrapy.Field()
