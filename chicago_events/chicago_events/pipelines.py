# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime
import json
import os


class JsonExportPipeline:
    def __init__(self):
        self.items = []
        self.file_path = 'chicago_events_data.json'
        
    def process_item(self, item, spider):
        self.items.append(dict(item))
        return item
        
    def close_spider(self, spider):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.items, f, ensure_ascii=False, indent=4)
        spider.logger.info(f"Exported {len(self.items)} items to {self.file_path}")


class PostgresPipeline:
    def __init__(self):
        self.engine = create_engine('postgresql://postgres.mbbndhtlnpsaltzgmdvd:vutran41@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres')
        self.metadata = MetaData()
        self.table = Table('events', self.metadata, autoload_with=self.engine)
        self.success_count = 0
        self.error_count = 0

    def process_item(self, item, spider):
        try:
            # Ensure start_date is not None
            if not item.get('start_date'):
                today = datetime.now()
                item['start_date'] = today.strftime('%Y-%m-%d')
                
            with self.engine.connect() as conn:
                stmt = insert(self.table).values(
                    event_id=item.get('event_id'),
                    name=item.get('name'),
                    description=item.get('description'),
                    url=item.get('url'),
                    status=item.get('status'),
                    start_date=item.get('start_date'),
                    start_time=item.get('start_time'),
                    venue_name=item.get('venue_name'),
                    venue_address=item.get('venue_address'),
                    venue_city=item.get('venue_city'),
                    venue_state=item.get('venue_state'),
                    venue_country=item.get('venue_country'),
                    venue_location_latitude=item.get('venue_location_latitude'),
                    venue_location_longitude=item.get('venue_location_longitude'),
                    price_min=item.get('price_min'),
                    price_max=item.get('price_max'),
                    image_url=item.get('image_url'),
                    categories=item.get('categories', []),
                    source=item.get('source', 'choosechicago')
                )
                
                # Handle conflicts by updating existing records
                stmt = stmt.on_conflict_do_update(
                    constraint='events_event_id_key',
                    set_={
                        'name': stmt.excluded.name,
                        'description': stmt.excluded.description,
                        'updatedAt': datetime.now()
                    }
                )
                
                conn.execute(stmt)
                conn.commit()
                self.success_count += 1
        except Exception as e:
            self.error_count += 1
            spider.logger.error(f"Error saving item to database: {e}")
            # Continue processing other items even if this one fails
        
        return item
        
    def close_spider(self, spider):
        spider.logger.info(f"Successfully saved {self.success_count} items to database")
        if self.error_count > 0:
            spider.logger.warning(f"Failed to save {self.error_count} items to database")
