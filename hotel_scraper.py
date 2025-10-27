import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging
import os
from typing import Optional, Dict, Any
import re
from datetime import datetime

class BookingHotelScraper:
    """
    A scraper for extracting hotel prices from Booking.com
    """
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self.setup_logging()
    
    def setup_logging(self):
        """Set up logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_driver(self):
        """Set up Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            # Try to get the ChromeDriver path and fix common issues
            driver_path = ChromeDriverManager().install()
            
            # Check if the path points to the correct executable
            if not os.path.isfile(driver_path) or not os.access(driver_path, os.X_OK):
                # Try to find the actual chromedriver executable in the directory
                driver_dir = os.path.dirname(driver_path)
                for root, dirs, files in os.walk(driver_dir):
                    for file in files:
                        if file == 'chromedriver' and os.access(os.path.join(root, file), os.X_OK):
                            driver_path = os.path.join(root, file)
                            self.logger.info(f"Found chromedriver at: {driver_path}")
                            break
                    if driver_path.endswith('chromedriver'):
                        break
            
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
        except Exception as e:
            self.logger.error(f"Failed to setup ChromeDriver: {str(e)}")
            # Fallback: try to use system chromedriver
            try:
                self.logger.info("Trying to use system chromedriver...")
                service = Service()  # Use system chromedriver
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            except Exception as fallback_error:
                self.logger.error(f"Fallback also failed: {str(fallback_error)}")
                raise Exception(f"Could not initialize ChromeDriver. Original error: {str(e)}, Fallback error: {str(fallback_error)}")
    
    def scrape_hotel_price(self, url: str) -> Dict[str, Any]:
        """
        Scrape hotel price information from a Booking.com URL
        
        Args:
            url (str): The Booking.com hotel URL
            
        Returns:
            Dict[str, Any]: Dictionary containing price and hotel information
        """
        if not self.driver:
            self.setup_driver()
        
        try:
            self.logger.info(f"Scraping hotel price from: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Try to close any popup dialogs
            try:
                close_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='header-banner-close-button']"))
                )
                close_button.click()
                time.sleep(1)
            except:
                pass
            
            # Extract hotel information
            hotel_info = self._extract_hotel_info()
            
            # Extract price information
            price_info = self._extract_price_info()
            
            # Combine all information
            result = {
                **hotel_info,
                **price_info,
                'scraped_at': datetime.now().isoformat(),
                'url': url
            }
            
            self.logger.info(f"Successfully scraped hotel: {result.get('hotel_name', 'Unknown')}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error scraping hotel price: {str(e)}")
            return {
                'error': str(e),
                'scraped_at': datetime.now().isoformat(),
                'url': url
            }
    
    def _extract_hotel_info(self) -> Dict[str, str]:
        """Extract basic hotel information"""
        hotel_info = {}
        
        try:
            # Hotel name
            hotel_name = self.driver.find_element(By.CSS_SELECTOR, "h2[data-testid='header-title']")
            hotel_info['hotel_name'] = hotel_name.text.strip()
        except:
            try:
                hotel_name = self.driver.find_element(By.CSS_SELECTOR, ".pp-header__title")
                hotel_info['hotel_name'] = hotel_name.text.strip()
            except:
                hotel_info['hotel_name'] = "Unknown"
        
        try:
            # Hotel address/location
            address = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='address']")
            hotel_info['address'] = address.text.strip()
        except:
            hotel_info['address'] = "Unknown"
        
        try:
            # Rating
            rating = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='review-score-component'] .ac78a73c96")
            hotel_info['rating'] = rating.text.strip()
        except:
            hotel_info['rating'] = "No rating"
        
        return hotel_info
    
    def _extract_price_info(self) -> Dict[str, Any]:
        """Extract price information"""
        price_info = {}
        
        # Try multiple selectors for price
        price_selectors = [
            "[data-testid='price-and-discounted-price'] .prco-valign-middle-helper",
            ".prco-valign-middle-helper",
            ".bui-price-display__value",
            ".sr-card__price--urgency .bui-price-display__value",
            ".bui-price-display__original",
            "[data-testid='price-and-discounted-price']"
        ]
        
        for selector in price_selectors:
            try:
                price_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if price_elements:
                    for element in price_elements:
                        price_text = element.text.strip()
                        if price_text and any(char.isdigit() for char in price_text):
                            price_info['raw_price'] = price_text
                            price_info['cleaned_price'] = self._clean_price(price_text)
                            break
                    if 'raw_price' in price_info:
                        break
            except:
                continue
        
        # Try to extract dates
        try:
            checkin_element = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='date-display-field-start']")
            checkout_element = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='date-display-field-end']")
            price_info['checkin_date'] = checkin_element.text.strip()
            price_info['checkout_date'] = checkout_element.text.strip()
        except:
            price_info['checkin_date'] = "Unknown"
            price_info['checkout_date'] = "Unknown"
        
        # Try to extract number of nights
        try:
            nights_element = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='price-summary'] .bp-price-summary__duration")
            price_info['nights'] = nights_element.text.strip()
        except:
            price_info['nights'] = "Unknown"
        
        return price_info
    
    def _clean_price(self, price_text: str) -> Optional[float]:
        """Clean and convert price text to float"""
        try:
            # Remove currency symbols and extra text, keep only digits, commas, and dots
            cleaned = re.sub(r'[^\d.,]', '', price_text)
            
            # Handle different decimal separators
            if ',' in cleaned and '.' in cleaned:
                # If both comma and dot present, assume comma is thousands separator
                cleaned = cleaned.replace(',', '')
            elif ',' in cleaned and len(cleaned.split(',')[-1]) == 3:
                # If comma is followed by exactly 3 digits, it's likely thousands separator
                cleaned = cleaned.replace(',', '')
            elif ',' in cleaned and len(cleaned.split(',')[-1]) <= 2:
                # If comma is followed by 1-2 digits, it's likely decimal separator
                cleaned = cleaned.replace(',', '.')
            
            return float(cleaned)
        except:
            return None
    
    def close(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
