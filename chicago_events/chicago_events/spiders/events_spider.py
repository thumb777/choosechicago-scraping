import scrapy
import re
from datetime import datetime
from hashlib import sha256  # To generate a unique hash
from ..items import ChicagoEventItem


class ChicagoEventsSpider(scrapy.Spider):
    name = 'chicago_events'
    allowed_domains = ['choosechicago.com']
    start_urls = ['https://www.choosechicago.com/events/']

    def start_requests(self):
        """
        Generates requests for each page of events.
        Adjust the range to include all pages of events.
        """
        for page in range(1, 50):  # Adjust the range to match the total number of pages
            url = f'https://www.choosechicago.com/events/page/{page}/'
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        """
        Parses the events on a single page.
        """
        # Select all event containers
        events = response.css('dd.js-group-events-day div.type-tribe_events')
        self.logger.info(f"Found {len(events)} events on {response.url}")

        if not events:
            self.logger.warning(f"No events found on {response.url}. Check your selectors or page structure.")

        for event in events:
            item = ChicagoEventItem()

            # Extract event URL
            event_url = event.css('a.card-img-link::attr(href)').get()
            if not event_url:
                continue  # Skip events without a valid URL

            item['url'] = event_url

            # Basic event information
            event_name = event.css('h4.card-title a::text').get('').strip()
            item['name'] = event_name
            item['description'] = event.css('div.card-body p::text').get('').strip()

            # Get the image URL
            item['image_url'] = event.css('a.card-img-link img::attr(data-src)').get()

            # Categories
            categories = event.css('h6.subtitle a::text').getall()
            item['categories'] = [cat.strip() for cat in categories if cat.strip()]

            # Extract date from the event-date-badge element
            month_elem = event.css('div.event-date-badge span.month::text').get()
            day_elem = event.css('div.event-date-badge span.date::text').get()
            start_date = None

            if month_elem and day_elem:
                # Map month names to numbers
                month_map = {
                    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
                }
                try:
                    month_num = month_map.get(month_elem.strip(), 1)
                    day_num = int(day_elem.strip())
                    current_year = datetime.now().year  # Assume the current year
                    start_date = f"{current_year}-{month_num:02d}-{day_num:02d}"
                    item['start_date'] = start_date
                except (ValueError, TypeError):
                    self.logger.warning(f"Failed to parse date for event: {event_url}")
                    item['start_date'] = None
            else:
                self.logger.warning(f"Missing date information for event: {event_url}")
                item['start_date'] = None

            # Extract venue information
            venue_name = None
            venue_info = event.css('div.tribe-events-venue-details')
            if venue_info:
                venue_name_elem = venue_info.css('b::text')
                if venue_name_elem:
                    venue_name = venue_name_elem.get().strip()
                    item['venue_name'] = venue_name

                # Get address
                address_text = venue_info.xpath('text()').getall()
                if address_text:
                    full_address = ' '.join([t.strip() for t in address_text if t.strip()])
                    item['venue_address'] = full_address

                # Default location info
                item['venue_city'] = 'Chicago'
                item['venue_state'] = 'IL'
                item['venue_country'] = 'USA'
                item['venue_location_latitude'] = None
                item['venue_location_longitude'] = None

            # Generate a unique event ID
            unique_id_string = f"{event_name}-{start_date}-{venue_name}-{event_url}"
            item['event_id'] = sha256(unique_id_string.encode('utf-8')).hexdigest()

            # Add default or optional fields
            item['status'] = 'active'
            if not item.get('start_time'):
                item['start_time'] = None
            item['price_min'] = None
            item['price_max'] = None
            item['source'] = 'choosechicago'

            yield item