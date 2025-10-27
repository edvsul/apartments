#!/usr/bin/env python3
"""
Multi-country hotel price scraper using NordVPN
Based on the flights scraper pattern, this scrapes hotel prices from Booking.com
across different countries to compare regional pricing differences.
"""

import os
import time
import re
import random
import shutil
import uuid
import pandas as pd
import subprocess
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import tempfile
from selenium.webdriver.common.keys import Keys
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_nordvpn_countries():
    """Get list of available NordVPN countries."""
    try:
        print("Getting available NordVPN countries...")
        result = subprocess.run(['nordvpn', 'countries'], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            countries_text = result.stdout.strip()
            print(f"NordVPN countries output: {countries_text[:200]}...")
            
            countries = []
            
            if ',' in countries_text:
                # Comma-separated format
                countries = [country.strip() for country in countries_text.split(',') if country.strip()]
            else:
                # Line-separated format
                lines = countries_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('-') and not line.startswith('Available'):
                        parts = line.split()
                        for part in parts:
                            if len(part) > 2 and part.isalpha():
                                countries.append(part)
            
            # Remove duplicates and filter valid country names
            unique_countries = []
            seen = set()
            for country in countries:
                country_clean = country.strip().replace(',', '').replace('.', '')
                if (len(country_clean) > 2 and
                    country_clean.isalpha() and
                    country_clean.lower() not in seen and
                    country_clean.lower() not in ['available', 'countries', 'nordvpn']):
                    unique_countries.append(country_clean)
                    seen.add(country_clean.lower())
            
            print(f"Found {len(unique_countries)} available countries: {unique_countries[:10]}...")
            return unique_countries
        else:
            print(f"Error getting NordVPN countries: {result.stderr}")
            return []
            
    except subprocess.TimeoutExpired:
        print("Timeout getting NordVPN countries")
        return []
    except Exception as e:
        print(f"Error getting NordVPN countries: {e}")
        return []

def connect_to_nordvpn_country(country):
    """Connect to a specific NordVPN country."""
    try:
        print(f"Connecting to NordVPN country: {country}")
        result = subprocess.run(['nordvpn', 'connect', country], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(f"Successfully connected to {country}")
            print(f"Connection output: {result.stdout.strip()}")
            
            # Wait for connection to stabilize
            time.sleep(10)
            
            # Verify connection
            status_result = subprocess.run(['nordvpn', 'status'], capture_output=True, text=True, timeout=30)
            if status_result.returncode == 0:
                print(f"Connection status: {status_result.stdout.strip()}")
            
            return True
        else:
            print(f"Failed to connect to {country}: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"Timeout connecting to {country}")
        return False
    except Exception as e:
        print(f"Error connecting to {country}: {e}")
        return False

def disconnect_nordvpn():
    """Disconnect from NordVPN."""
    try:
        print("Disconnecting from NordVPN...")
        result = subprocess.run(['nordvpn', 'disconnect'], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("Successfully disconnected from NordVPN")
            print(f"Disconnect output: {result.stdout.strip()}")
            time.sleep(5)
            return True
        else:
            print(f"Error disconnecting from NordVPN: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("Timeout disconnecting from NordVPN")
        return False
    except Exception as e:
        print(f"Error disconnecting from NordVPN: {e}")
        return False

def get_current_ip():
    """Get current IP address to verify VPN connection."""
    try:
        result = subprocess.run(["curl", "-s", "https://ipinfo.io/ip"], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        return "Unknown"
    except:
        return "Unknown"

def setup_clean_driver():
    """Set up and return a configured Chrome WebDriver with clean session."""
    chrome_options = Options()
    
    # Essential options for headless operation
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Create unique temporary directory
    unique_id = str(uuid.uuid4())[:8]
    timestamp = str(int(time.time()))
    temp_dir_name = f"hotel_chrome_session_{timestamp}_{unique_id}"
    temp_dir = os.path.join(os.getcwd(), "temp_chrome_sessions", temp_dir_name)
    os.makedirs(temp_dir, exist_ok=True)
    chrome_options.add_argument(f"--user-data-dir={temp_dir}")
    
    # Ensure completely clean session
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--disable-application-cache")
    chrome_options.add_argument("--disable-background-networking")
    chrome_options.add_argument("--disable-sync")
    chrome_options.add_argument("--disable-translate")
    chrome_options.add_argument("--hide-scrollbars")
    chrome_options.add_argument("--metrics-recording-only")
    chrome_options.add_argument("--mute-audio")
    chrome_options.add_argument("--no-default-browser-check")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--safebrowsing-disable-auto-update")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--disable-domain-reliability")
    
    # User agent randomization
    chrome_versions = ["120.0.0.0", "119.0.0.0", "121.0.0.0"]
    chrome_version = random.choice(chrome_versions)
    chrome_options.add_argument(f"--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36")
    
    # Exclude automation flags
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # Additional prefs for clean session
    prefs = {
        "profile.default_content_setting_values": {
            "notifications": 2,
            "geolocation": 2,
        },
        "profile.managed_default_content_settings": {
            "images": 1
        },
        "profile.default_content_settings": {
            "popups": 0
        }
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    # Create WebDriver with fallback mechanism
    try:
        driver_path = ChromeDriverManager().install()
        
        # Check if the path points to the correct executable
        if not os.path.isfile(driver_path) or not os.access(driver_path, os.X_OK):
            # Try to find the actual chromedriver executable
            driver_dir = os.path.dirname(driver_path)
            for root, dirs, files in os.walk(driver_dir):
                for file in files:
                    if file == 'chromedriver' and os.access(os.path.join(root, file), os.X_OK):
                        driver_path = os.path.join(root, file)
                        logger.info(f"Found chromedriver at: {driver_path}")
                        break
                if driver_path.endswith('chromedriver'):
                    break
        
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
    except Exception as e:
        logger.error(f"Failed to setup ChromeDriver: {str(e)}")
        # Fallback: try to use system chromedriver
        try:
            logger.info("Trying to use system chromedriver...")
            service = Service()
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as fallback_error:
            logger.error(f"Fallback also failed: {str(fallback_error)}")
            raise Exception(f"Could not initialize ChromeDriver. Original error: {str(e)}, Fallback error: {str(fallback_error)}")
    
    # Remove webdriver property and other automation indicators
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_script("delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array")
    driver.execute_script("delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise")
    driver.execute_script("delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol")
    
    print(f"Created clean browser session with temp directory: {temp_dir}")
    
    # Store temp_dir in driver for cleanup later
    driver.temp_dir = temp_dir
    return driver

def extract_hotel_info_and_price(driver):
    """Extract hotel information and price from Booking.com page."""
    hotel_data = {}
    
    try:
        # Hotel name
        hotel_name_selectors = [
            "h2[data-testid='header-title']",
            ".pp-header__title",
            "h1[data-testid='title']",
            "h1.hp__hotel-name"
        ]
        
        for selector in hotel_name_selectors:
            try:
                hotel_name = driver.find_element(By.CSS_SELECTOR, selector)
                hotel_data['hotel_name'] = hotel_name.text.strip()
                break
            except:
                continue
        
        if 'hotel_name' not in hotel_data:
            hotel_data['hotel_name'] = "Unknown"
        
        # Hotel address/location
        try:
            address = driver.find_element(By.CSS_SELECTOR, "[data-testid='address']")
            hotel_data['address'] = address.text.strip()
        except:
            hotel_data['address'] = "Unknown"
        
        # Rating
        try:
            rating = driver.find_element(By.CSS_SELECTOR, "[data-testid='review-score-component'] .ac78a73c96")
            hotel_data['rating'] = rating.text.strip()
        except:
            hotel_data['rating'] = "No rating"
        
        # Extract price information
        price_selectors = [
            "[data-testid='price-and-discounted-price'] .prco-valign-middle-helper",
            ".prco-valign-middle-helper",
            ".bui-price-display__value",
            ".sr-card__price--urgency .bui-price-display__value",
            ".bui-price-display__original",
            "[data-testid='price-and-discounted-price']",
            ".bui-price-display__label",
            ".prco-text-nowrap-helper"
        ]
        
        for selector in price_selectors:
            try:
                price_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if price_elements:
                    for element in price_elements:
                        price_text = element.text.strip()
                        if price_text and any(char.isdigit() for char in price_text):
                            hotel_data['raw_price'] = price_text
                            hotel_data['cleaned_price'] = clean_price(price_text)
                            break
                    if 'raw_price' in hotel_data:
                        break
            except:
                continue
        
        # Try to extract dates
        try:
            checkin_element = driver.find_element(By.CSS_SELECTOR, "[data-testid='date-display-field-start']")
            checkout_element = driver.find_element(By.CSS_SELECTOR, "[data-testid='date-display-field-end']")
            hotel_data['checkin_date'] = checkin_element.text.strip()
            hotel_data['checkout_date'] = checkout_element.text.strip()
        except:
            hotel_data['checkin_date'] = "Unknown"
            hotel_data['checkout_date'] = "Unknown"
        
        # Try to extract number of nights
        try:
            nights_element = driver.find_element(By.CSS_SELECTOR, "[data-testid='price-summary'] .bp-price-summary__duration")
            hotel_data['nights'] = nights_element.text.strip()
        except:
            hotel_data['nights'] = "Unknown"
        
        return hotel_data
        
    except Exception as e:
        logger.error(f"Error extracting hotel info: {str(e)}")
        return {
            'hotel_name': 'Unknown',
            'address': 'Unknown',
            'rating': 'Unknown',
            'raw_price': 'No price found',
            'cleaned_price': None,
            'checkin_date': 'Unknown',
            'checkout_date': 'Unknown',
            'nights': 'Unknown'
        }

def clean_price(price_text):
    """Clean and convert price text to float."""
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

def handle_booking_popups(driver):
    """Handle various popups that might appear on Booking.com."""
    try:
        # Common popup close button selectors
        popup_selectors = [
            "[data-testid='header-banner-close-button']",
            ".bui-modal__close",
            ".bui-button--close",
            "[aria-label='Close']",
            ".close-button",
            ".modal-close"
        ]
        
        for selector in popup_selectors:
            try:
                close_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                close_button.click()
                time.sleep(1)
                logger.info(f"Closed popup using selector: {selector}")
                return True
            except:
                continue
        
        return False
    except:
        return False

def scrape_hotel_for_country(hotel_url, country):
    """Scrape hotel price for a specific country using VPN."""
    driver = setup_clean_driver()
    
    try:
        logger.info(f"Scraping hotel for country: {country}")
        logger.info(f"Current IP: {get_current_ip()}")
        
        # Navigate to the hotel URL
        driver.get(hotel_url)
        time.sleep(5)
        
        # Handle any popups
        handle_booking_popups(driver)
        
        # Wait for page to load
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except TimeoutException:
            logger.warning("Timeout waiting for page to load")
        
        time.sleep(3)
        
        # Extract hotel information and price
        hotel_data = extract_hotel_info_and_price(driver)
        hotel_data['country'] = country
        hotel_data['scraped_at'] = datetime.now().isoformat()
        hotel_data['url'] = hotel_url
        hotel_data['ip_address'] = get_current_ip()
        
        # Take screenshot
        os.makedirs("screenshots", exist_ok=True)
        screenshot_file = f"screenshots/hotel_{country}_{int(time.time())}.png"
        driver.save_screenshot(screenshot_file)
        hotel_data['screenshot'] = screenshot_file
        
        logger.info(f"Successfully scraped hotel data for {country}: {hotel_data.get('hotel_name', 'Unknown')} - {hotel_data.get('raw_price', 'No price')}")
        
        return hotel_data
        
    except Exception as e:
        logger.error(f"Error scraping hotel for {country}: {str(e)}")
        return {
            'country': country,
            'hotel_name': 'Error',
            'address': 'Error',
            'rating': 'Error',
            'raw_price': f'Error: {str(e)}',
            'cleaned_price': None,
            'checkin_date': 'Error',
            'checkout_date': 'Error',
            'nights': 'Error',
            'scraped_at': datetime.now().isoformat(),
            'url': hotel_url,
            'ip_address': get_current_ip(),
            'screenshot': None
        }
    
    finally:
        # Cleanup
        temp_dir = getattr(driver, 'temp_dir', None)
        try:
            driver.quit()
        except:
            pass
        
        # Clean up temporary directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.info(f"Cleaned up temp directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Could not clean up temp directory {temp_dir}: {e}")

def cleanup_old_temp_dirs():
    """Clean up any leftover Chrome temp directories from previous runs."""
    try:
        temp_base = os.path.join(os.getcwd(), "temp_chrome_sessions")
        if os.path.exists(temp_base):
            for item in os.listdir(temp_base):
                if item.startswith("hotel_chrome_session_"):
                    temp_path = os.path.join(temp_base, item)
                    if os.path.isdir(temp_path):
                        try:
                            shutil.rmtree(temp_path, ignore_errors=True)
                            logger.info(f"Cleaned up leftover temp directory: {temp_path}")
                        except:
                            pass
            # Remove the temp_chrome_sessions directory if it's empty
            try:
                if not os.listdir(temp_base):
                    os.rmdir(temp_base)
                    logger.info("Removed empty temp_chrome_sessions directory")
            except:
                pass
    except Exception as e:
        logger.warning(f"Could not clean up old temp directories: {e}")

def main():
    """Main function to run multi-country hotel price comparison."""
    # Clean up any leftover temp directories first
    cleanup_old_temp_dirs()
    
    # Hotel URL from the user's request
    hotel_url = "https://www.booking.com/hotel/nz/goodview-serviced-apartment.html?aid=304142&label=gen173nr-10CAEoggI46AdIM1gEaD2IAQGYATO4AQfIAQzYAQPoAQH4AQGIAgGoAgG4As7u_scGwAIB0gIkYmRiODNhYmQtYTVlNy00OTljLThjZjgtNzg2OWJjMzU4ODBj2AIB4AIB&sid=161052f1d90c5a7f57b951c160f1fb7f&all_sr_blocks=218269713_273703546_0_0_0&checkin=2026-03-08&checkout=2026-03-22&dest_id=-1506909&dest_type=city&dist=0&group_adults=2&group_children=0&hapos=2&highlighted_blocks=218269713_273703546_0_0_0&hpos=2&matching_block_id=218269713_273703546_0_0_0&no_rooms=1&req_adults=2&req_children=0&room1=A%2CA&sb_price_type=total&sr_order=popularity&sr_pri_blocks=218269713_273703546_0_0_0__156889&srepoch=1761589637&srpvid=901281bb46be0113&type=total&ucfs=1&"
    
    print("🏨 Starting multi-country hotel price comparison...")
    print(f"🔗 Hotel URL: {hotel_url[:100]}...")
    print(f"📅 Check-in: 2026-03-08")
    print(f"📅 Check-out: 2026-03-22")
    print(f"👥 Guests: 2 adults")
    
    # Get available NordVPN countries
    countries = get_nordvpn_countries()
    if not countries:
        print("ERROR: No NordVPN countries available. NordVPN is required for this script.")
        print("Please ensure NordVPN is installed and you are logged in.")
        return
    else:
        print(f"Found {len(countries)} NordVPN countries to test: {countries}")
    
    all_hotel_data = []
    successful_countries = []
    failed_countries = []
    
    # Disconnect from any existing VPN connection
    disconnect_nordvpn()
    
    # Test a subset of countries (first 10) to avoid running too long
    test_countries = countries[:10]
    print(f"Testing first {len(test_countries)} countries: {test_countries}")
    
    for i, country in enumerate(test_countries, 1):
        print(f"\n{'='*60}")
        print(f"Processing country {i}/{len(test_countries)}: {country}")
        print(f"{'='*60}")
        
        # Connect to VPN
        if not connect_to_nordvpn_country(country):
            print(f"Failed to connect to {country}, skipping...")
            failed_countries.append(country)
            continue
        
        try:
            # Scrape hotel data for this country
            hotel_data = scrape_hotel_for_country(hotel_url, country)
            
            if hotel_data and hotel_data.get('raw_price') != 'No price found':
                all_hotel_data.append(hotel_data)
                successful_countries.append(country)
                print(f"✅ Successfully scraped data for {country}")
            else:
                print(f"❌ No valid data found for {country}")
                failed_countries.append(country)
                
        except Exception as e:
            print(f"❌ Error scraping data for {country}: {e}")
            failed_countries.append(country)
        
        # Brief pause between countries
        if i < len(test_countries):
            time.sleep(5)
    
    # Final VPN disconnect
    disconnect_nordvpn()
    
    # Save results
    if all_hotel_data:
        # Create DataFrame
        df = pd.DataFrame(all_hotel_data)
        
        # Save to CSV
        os.makedirs("hotel_prices", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = f"hotel_prices/goodview_hotel_multi_country_{timestamp}.csv"
        df.to_csv(csv_file, index=False)
        print(f"\n📊 Results saved to: {csv_file}")
        
        # Save to JSON for better readability
        json_file = f"hotel_prices/goodview_hotel_multi_country_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(all_hotel_data, f, indent=2, ensure_ascii=False)
        print(f"📊 Results also saved to: {json_file}")
        
        # Print summary
        print("\n" + "="*80)
        print("🏨 HOTEL PRICE SUMMARY BY COUNTRY")
        print("="*80)
        
        for hotel_data in all_hotel_data:
            country = hotel_data['country']
            price = hotel_data['raw_price']
            cleaned_price = hotel_data['cleaned_price']
            hotel_name = hotel_data['hotel_name']
            
            print(f"\n🌍 {country}:")
            print(f"  🏨 Hotel: {hotel_name}")
            print(f"  💰 Price: {price}")
            if cleaned_price:
                print(f"  💵 Numeric: {cleaned_price}")
            print(f"  🕐 Scraped: {hotel_data['scraped_at']}")
            print(f"  🌐 IP: {hotel_data['ip_address']}")
        
        print(f"\n\n📈 SUMMARY:")
        print(f"✅ Successful countries: {len(successful_countries)} - {successful_countries}")
        print(f"❌ Failed countries: {len(failed_countries)} - {failed_countries}")
        print(f"📊 Total hotel prices collected: {len(all_hotel_data)}")
        
        # Price comparison
        valid_prices = [data for data in all_hotel_data if data['cleaned_price'] is not None]
        if valid_prices:
            prices = [data['cleaned_price'] for data in valid_prices]
            min_price = min(prices)
            max_price = max(prices)
            avg_price = sum(prices) / len(prices)
            
            print(f"\n💰 PRICE ANALYSIS:")
            print(f"  Lowest price: {min_price}")
            print(f"  Highest price: {max_price}")
            print(f"  Average price: {avg_price:.2f}")
            print(f"  Price difference: {max_price - min_price:.2f}")
    
    else:
        print("\n❌ No hotel data was collected from any country.")
        print(f"Failed countries: {failed_countries}")

if __name__ == "__main__":
    main()
