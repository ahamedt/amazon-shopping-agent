from utils.data_models import ProductInfo, SearchPreferences
from typing import List
import logging

from .amazon_scraper import AmazonScraper
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ScraperManager:
    def __init__(self, headless=True):
        self.scraper = AmazonScraper(headless=True)
        self.is_initialized = False

    def ensure_initialized(self):
        if not self.is_initialized:
            logger.info("Initializing scraper...")
            self.scraper.start()
            self.scraper.navigate_to_amazon()
            self.is_initialized = True
            
    def close(self):
        """Close the scraper when it's no longer needed."""
        if self.is_initialized:
            logger.info("Closing scraper...")
            self.scraper.close()
            self.is_initialized = False
    
    def search_amazon(self, search_preferences: SearchPreferences) -> List[ProductInfo]:
        try: 
            self.ensure_initialized()
            products = self.scraper.search_products(search_preferences.query)
            return self._filter_products(products, search_preferences)
        except Exception as e:
            logger.error(f"Error during search: {e}")
            self.is_initialized = False
            return []
        
    def _filter_products(self, products: List[ProductInfo], preferences: SearchPreferences) -> List[ProductInfo]:
        filtered_products = []
        for product in products:
            if preferences.price_range.minPrice and product.price < preferences.price_range.minPrice:
                continue
            if preferences.price_range.maxPrice and product.price > preferences.price_range.maxPrice:
                continue
            if preferences.rating_range:
                if (preferences.rating_range.minRating is not None and 
                    product.rating < preferences.rating_range.minRating):
                    continue
                if (preferences.rating_range.maxRating is not None and 
                    product.rating > preferences.rating_range.maxRating):
                    continue
            if preferences.is_prime_eligible and not product.is_prime_eligible:
                continue
                
            filtered_products.append(product)
        return filtered_products