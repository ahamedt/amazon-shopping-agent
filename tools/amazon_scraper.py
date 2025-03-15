import time 
import logging
import random
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc
from utils.data_models import ProductInfo
from typing import List

logger = logging.getLogger(__name__)
logger.disabled = True

logging.getLogger('selenium').disabled = True
logging.getLogger('urllib3').disabled = True
logging.getLogger("httpx").disabled = True
logging.getLogger('openai').disabled = True
logging.getLogger('webdriver_manager').disabled = True

class AmazonScraper:
    def __init__(self, headless: bool = True):
            """
            Initialize the AmazonScraper with browser configuration.
            """
            self.driver = None
            self.headless = headless
            self.user_agent = self._get_random_user_agent()
            self.base_url = "https://www.amazon.com"

    def _get_random_user_agent(self) -> str:
        """
        Returns a random user agent from a predefined list.
        This helps avoid detection as a bot.
        """
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
        ]
        return random.choice(user_agents)
    
    def _search_for_product(self, product: str) -> None:
        try:
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "twotabsearchtextbox"))
            )
            search_box.clear()
            for char in product:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.05, 0.2))
            time.sleep(random.uniform(0.5, 1.5))
            search_box.submit()
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.s-result-item"))
            )
            time.sleep(random.uniform(1.0, 2.5))

        except Exception as e:
            logging.error(f"Error while searching for {product}: {e}")
            raise
        
          
    def _setup_undetected_driver(self):
        """
        Set up the undetected Chrome driver.
        """
        try:
            options = uc.ChromeOptions()
            if self.headless:
                options.add_argument('--headless')
                options.add_argument('--blink-settings=imagesEnabled=false')
            options.add_argument(f'user-agent={self.user_agent}')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            driver = uc.Chrome(options=options)
            driver.set_window_size(1920, 1080)
                
            return driver
        except Exception as e:
            logger.error(f"Error setting up undetected driver: {e}")
            raise
    
    def _setup_driver(self):
        """
        Set up the Selenium WebDriver with appropriate options.
        """
        options = Options()
        
        if self.headless:
            options.add_argument('--headless')
        
        options.add_argument(f'user-agent={self.user_agent}')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        
        prefs = {
            "profile.managed_default_content_settings.images": 2
        }
        options.add_experimental_option("prefs", prefs)
        
        try:
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options
            )
        
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return driver
        except Exception as e:
            logger.error(f"Error setting up WebDriver: {e}")
            raise

    
    def _extract_product_link(self, product_element) -> str:
        """
        Extract the product link from a product element.

        """
        try:
            link_selectors = [
                "a.a-link-normal.s-no-outline",
                "a.a-link-normal.a-text-normal",
                "h2 a",
                ".a-link-normal",
                "a[href*='/dp/']",
                "div[data-cy='title-recipe'] a"
            ]
            
            for selector in link_selectors:
                try:
                    link_element = product_element.find_element(By.CSS_SELECTOR, selector)
                    product_link = link_element.get_attribute("href")
                    if product_link and "/dp/" in product_link:
                        return product_link
                except:
                    continue
                    
            logging.warning("Could not find product link in element")
            return ""
            
        except Exception as e:
            logging.error(f"Error extracting product link: {e}")
            return ""

    def _get_product_results(self) -> List[ProductInfo]:
        """
        Extract product information by first collecting all product links,
        then visiting each product page individually.
        
        Returns:
            List[ProductInfo]: List of product information objects
        """
        logging.info("Extracting product results")
        products = []
        product_links = []
        
        logging.info("Collecting product links from search results")
        try:
            selectors = [
                "div.s-result-item[data-component-type='s-search-result']",
                "div.sg-col-4-of-24.sg-col-4-of-12",
                "div.sg-col-20-of-24.s-result-item",
                "div.s-result-item"
            ]
            
            product_elements = []
            for selector in selectors:
                product_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if product_elements:
                    logging.info(f"Found {len(product_elements)} products with selector: {selector}")
                    break
                    
            if not product_elements:
                logging.warning("No product elements found with any selector")
                return []
                
            for product_element in product_elements[:10]:
                link = self._extract_product_link(product_element)
                if link:
                    product_links.append(link)
                    
            logging.info(f"Collected {len(product_links)} product links")
            
        except Exception as e:
            logging.error(f"Error collecting product links: {e}")
            return []
        
        for i, link in enumerate(product_links):
            try:
                logging.info(f"Processing product {i+1}/{len(product_links)}")
                
                self.driver.get(link)
                
                time.sleep(random.uniform(2, 4))
                
                product_info = self._extract_product_info_from_page()
                
                if product_info:
                    products.append(product_info)
                    
                # A random delay between product visits to replicate human behavior
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                logging.error(f"Error processing product {i+1}: {e}")
                continue
        
        return products
    
    def _extract_product_info_from_page(self) -> Optional[ProductInfo]:
        """
        Extract all product information from a product detail page.
        """
        try:
            product_name = ""
            name_selectors = [
                "span#productTitle",
                "h1.a-size-large",
                "div.product-title"
            ]
            
            for selector in name_selectors:
                try:
                    name_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    product_name = name_element.text.strip()
                    if product_name:
                        break
                except:
                    continue
                    
            if not product_name:
                logging.warning("Could not find product name on page")
                product_name = "Unknown Product"
            
            price = 0.0
            price_selectors = [
                "span.a-price .a-offscreen",
                "span#priceblock_ourprice",
                "span#priceblock_dealprice",
                "span.a-price-whole"
            ]
            
            for selector in price_selectors:
                try:
                    price_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    price_text = price_element.text
                    if not price_text:
                        price_text = price_element.get_attribute("innerHTML")
                        
                    price_text = price_text.replace("$", "").replace(",", "").strip()
                    price = float(price_text)
                    break
                except:
                    continue

            rating = 0.0
            rating_selectors = [
                "span.a-icon-alt",
                "i.a-icon-star span.a-icon-alt",
                "#acrPopover .a-icon-alt"
            ]
            
            for selector in rating_selectors:
                try:
                    rating_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    rating_text = rating_element.text or rating_element.get_attribute("innerHTML")
                    rating = float(rating_text.split(" ")[0])
                    break
                except:
                    continue
            
            is_prime_eligible = False
            prime_selectors = [
                "i.a-icon-prime",
                ".a-icon-prime",
                "span.a-icon-prime"
            ]
            
            for selector in prime_selectors:
                try:
                    prime_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if prime_element:
                        is_prime_eligible = True
                        break
                except:
                    continue
            
            # Extract description
            description = ""
            desc_selectors = [
                "#productDescription p",
                "#feature-bullets .a-list-item",
                "#aplus p",
                "div[data-cel-widget='productDescription'] p"
            ]
            
            for selector in desc_selectors:
                try:
                    desc_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    desc_parts = []
                    for element in desc_elements:
                        text = element.text.strip()
                        if text:
                            desc_parts.append(text)
                            
                    if desc_parts:
                        description = "\n".join(desc_parts)
                        break
                except:
                    continue
            
            reviews = []
            logging.info("Extracting visible reviews from product page")
            

            review_selectors = [
                "div[data-hook='review-body']",
                "div[data-hook='review-body'] span",
                "span[data-hook='review-body']",
                ".review-text-content span"
            ]
            
            for selector in review_selectors:
                try:
                    review_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    logging.info(f"Found {len(review_elements)} review elements with selector: {selector}")
                    
                    for element in review_elements[:5]:
                        review_text = element.text.strip()
                        if review_text and len(review_text) > 10:
                            reviews.append(review_text)
                            
                    if reviews:
                        logging.info(f"Successfully extracted {len(reviews)} reviews")
                        break
                except Exception as e:
                    logging.warning(f"Error with review selector {selector}: {e}")
                    continue
            return ProductInfo(
                product_name=product_name,
                price=price,
                rating=rating,
                is_prime_eligible=is_prime_eligible,
                description=description if description else None,
                reviews=reviews if reviews else None
            )
            
        except Exception as e:
            logging.error(f"Error extracting product info from page: {e}")
            return None


    def start(self) -> bool:
            """
            Initialize and start the WebDriver.
            """
            try:
                if self.driver is not None:
                    logger.warning("Driver already started. Call close() first to restart.")
                    return False
                
                logger.info("Starting WebDriver...")
                self.driver = self._setup_driver()
                return True
            except Exception as e:
                logger.error(f"Failed to start WebDriver: {e}")
                return False

    def navigate_to_amazon(self) -> bool:
            """
            Navigate to the Amazon homepage.
            """
            if self.driver is None:
                logger.error("Driver not started. Call start() first.")
                return False
            
            try:
                logger.info(f"Navigating to {self.base_url}")
                self.driver.get(self.base_url)
                
                time.sleep(random.uniform(2, 5))
                
                if "Amazon" in self.driver.title:
                    logger.info("Successfully navigated to Amazon")
                    return True
                else:
                    logger.warning(f"Navigation seems off: Title is '{self.driver.title}'")
                    return False
            except WebDriverException as e:
                logger.error(f"Navigation error: {e}")
                return False
            
    def search_products(self, search_term: str, start_new_session: bool = True) -> List[ProductInfo]:
        """
        Search for products and return the product information.
        """
        driver_started = False
        
        try:
            if start_new_session:
                if self.driver is not None:
                    self.close()
                
                if not self.start():
                    logging.error("Failed to start the WebDriver")
                    return []
                driver_started = True
                
                if not self.navigate_to_amazon():
                    logging.error("Failed to navigate to Amazon")
                    return []
            
            self._search_for_product(search_term)

            products = self._get_product_results()
            logger.info(f"[search_products] Found {len(products)} products: {products}")
            
            return products
        
        except Exception as e:
            logging.error(f"Error searching for products: {e}")
            return []
        
        finally:
            if start_new_session and driver_started:
                self.close()

    def close(self):
            """
            Close the WebDriver and release resources.
            """
            if self.driver is not None:
                logger.info("Closing WebDriver...")
                try:
                    self.driver.quit()
                except Exception as e:
                    logger.error(f"Error closing driver: {e}")
                finally:
                    self.driver = None