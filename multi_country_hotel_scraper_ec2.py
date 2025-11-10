#!/usr/bin/env python3
"""
EC2-optimized multi-country hotel price scraper using NordVPN
Specifically designed for Amazon Linux EC2 instances
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
import boto3
from botocore.exceptions import ClientError
import pymysql

# Set up logging for EC2
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hotel_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def insert_hotel_data_to_dynamodb(all_hotel_data):
    """Insert hotel data into DynamoDB"""
    try:
        dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
        table = dynamodb.Table('scraper')

        for data in all_hotel_data:
            table.put_item(
                Item={
                    'pk': {'S': data.get('country')},
                    'sk': {'S': data.get('scraped_at')}
                })

    except Exception as e:
        logger.error(f"Error inserting hotel data to DynamoDB: {e}")
        return False

# # RDS Configuration
# RDS_HOST = "scraper.clyuc4e6ci6m.eu-west-1.rds.amazonaws.com"
# RDS_PORT = 3306
# RDS_DB_NAME = "hotel_scraper"
# RDS_USERNAME = "iam_db_user"
# RDS_REGION = "eu-west-1"

# def get_rds_iam_token():
#     """Generate an IAM authentication token for RDS"""
#     try:
#         rds_client = boto3.client('rds', region_name=RDS_REGION)
#         token = rds_client.generate_db_auth_token(
#             DBHostname=RDS_HOST,
#             Port=RDS_PORT,
#             DBUsername=RDS_USERNAME,
#             Region=RDS_REGION
#         )
#         return token
#     except Exception as e:
#         logger.error(f"Error generating RDS IAM token: {e}")
#         return None

# def get_rds_connection():
#     """Get RDS connection using IAM authentication"""
#     try:
#         token = get_rds_iam_token()
#         if not token:
#             logger.error("Failed to generate IAM token")
#             return None

#         ssl_ca = '/home/ssm-user/global-bundle.pem'  # RDS CA certificate

#         connection = pymysql.connect(
#             host=RDS_HOST,
#             user=RDS_USERNAME,
#             password=token,
#             database=RDS_DB_NAME,
#             port=RDS_PORT,
#             ssl_ca=ssl_ca,
#             ssl_verify_cert=True,
#             ssl_verify_identity=True,
#             connect_timeout=10
#         )
#         logger.info("Successfully connected to RDS using IAM authentication")
#         return connection
#     except pymysql.MySQLError as e:
#         logger.error(f"MySQL error connecting to RDS: {e}")
#         return None
#     except Exception as e:
#         logger.error(f"Error connecting to RDS: {e}")
#         return None

# def create_hotel_prices_table():
#     """Create hotel_prices table if it doesn't exist"""
#     try:
#         connection = get_rds_connection()
#         if not connection:
#             return False

#         with connection.cursor() as cursor:
#             create_table_query = """
#             CREATE TABLE IF NOT EXISTS hotel_prices (
#                 id INT AUTO_INCREMENT PRIMARY KEY,
#                 country VARCHAR(100),
#                 hotel_name VARCHAR(500),
#                 address TEXT,
#                 rating VARCHAR(50),
#                 raw_price VARCHAR(100),
#                 cleaned_price DECIMAL(10,2),
#                 checkin_date VARCHAR(50),
#                 checkout_date VARCHAR(50),
#                 nights VARCHAR(50),
#                 scraped_at TIMESTAMP,
#                 url TEXT,
#                 ip_address VARCHAR(50),
#                 screenshot_path VARCHAR(500),
#                 screenshot_s3_url TEXT,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                 INDEX idx_country (country),
#                 INDEX idx_scraped_at (scraped_at)
#             ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
#             """
#             cursor.execute(create_table_query)
#             connection.commit()
#             logger.info("Hotel prices table created or already exists")

#         connection.close()
#         return True
#     except Exception as e:
#         logger.error(f"Error creating hotel_prices table: {e}")
#         return False

# def insert_hotel_data_to_rds(hotel_data):
#     """Insert hotel data into RDS"""
#     try:
#         connection = get_rds_connection()
#         if not connection:
#             logger.error("Failed to get RDS connection for insert")
#             return False

#         with connection.cursor() as cursor:
#             insert_query = """
#             INSERT INTO hotel_prices
#             (country, hotel_name, address, rating, raw_price, cleaned_price,
#              checkin_date, checkout_date, nights, scraped_at, url, ip_address,
#              screenshot_path, screenshot_s3_url)
#             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#             """

#             values = (
#                 hotel_data.get('country'),
#                 hotel_data.get('hotel_name'),
#                 hotel_data.get('address'),
#                 hotel_data.get('rating'),
#                 hotel_data.get('raw_price'),
#                 hotel_data.get('cleaned_price'),
#                 hotel_data.get('checkin_date'),
#                 hotel_data.get('checkout_date'),
#                 hotel_data.get('nights'),
#                 hotel_data.get('scraped_at'),
#                 hotel_data.get('url'),
#                 hotel_data.get('ip_address'),
#                 hotel_data.get('screenshot'),
#                 hotel_data.get('screenshot_s3_url')
#             )

#             cursor.execute(insert_query, values)
#             connection.commit()
#             logger.info(f"Successfully inserted hotel data for {hotel_data.get('country')} into RDS")

#         connection.close()
#         return True
#     except Exception as e:
#         logger.error(f"Error inserting hotel data to RDS: {e}")
#         return False

def upload_screenshot_to_s3(local_file_path, bucket_name="apartmentscreenshots"):
    """Upload a screenshot file to S3 bucket"""
    try:
        # Create S3 client
        s3_client = boto3.client('s3')

        # Extract filename from path
        filename = os.path.basename(local_file_path)

        # Create S3 key with timestamp prefix for organization
        timestamp_prefix = datetime.now().strftime("%Y/%m/%d")
        s3_key = f"hotel-scraper/{timestamp_prefix}/{filename}"

        # Upload file
        logger.info(f"Uploading {filename} to S3 bucket {bucket_name}")
        s3_client.upload_file(local_file_path, bucket_name, s3_key)

        # Generate S3 URL
        s3_url = f"s3://{bucket_name}/{s3_key}"
        logger.info(f"Screenshot uploaded successfully: {s3_url}")

        return s3_url

    except ClientError as e:
        logger.error(f"Failed to upload screenshot to S3: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error uploading to S3: {e}")
        return None

def get_nordvpn_countries():
    """Get list of available NordVPN countries - EC2 optimized."""
    try:
        logger.info("Getting available NordVPN countries...")

        # First check if NordVPN daemon is running
        daemon_check = subprocess.run(['systemctl', 'is-active', 'nordvpnd'],
                                    capture_output=True, text=True)
        if daemon_check.returncode != 0:
            logger.info("Starting NordVPN daemon...")
            subprocess.run(['sudo', 'systemctl', 'start', 'nordvpnd'], check=False)
            time.sleep(5)

        result = subprocess.run(['nordvpn', 'countries'], capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            countries_text = result.stdout.strip()
            logger.info(f"NordVPN countries output: {countries_text[:200]}...")

            countries = []

            if ',' in countries_text:
                countries = [country.strip() for country in countries_text.split(',') if country.strip()]
            else:
                lines = countries_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('-') and not line.startswith('Available'):
                        parts = line.split()
                        for part in parts:
                            if len(part) > 2 and part.isalpha():
                                countries.append(part)

            # Filter and clean country names
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

            logger.info(f"Found {len(unique_countries)} available countries")
            return unique_countries[:1]
        else:
            logger.error(f"Error getting NordVPN countries: {result.stderr}")
            return []

    except subprocess.TimeoutExpired:
        logger.error("Timeout getting NordVPN countries")
        return []
    except Exception as e:
        logger.error(f"Error getting NordVPN countries: {e}")
        return []

def connect_to_nordvpn_country(country):
    """Connect to a specific NordVPN country - EC2 optimized."""
    try:
        logger.info(f"Connecting to NordVPN country: {country}")

        # Disconnect first
        subprocess.run(['nordvpn', 'disconnect'], capture_output=True, text=True, timeout=30)
        time.sleep(3)

        # Connect to country
        result = subprocess.run(['nordvpn', 'connect', country], capture_output=True, text=True, timeout=90)

        if result.returncode == 0:
            logger.info(f"Successfully connected to {country}")

            # Wait longer for EC2 connection to stabilize
            time.sleep(15)

            # Verify connection
            status_result = subprocess.run(['nordvpn', 'status'], capture_output=True, text=True, timeout=30)
            if status_result.returncode == 0:
                logger.info(f"Connection status: {status_result.stdout.strip()}")

            return True
        else:
            logger.error(f"Failed to connect to {country}: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        logger.error(f"Timeout connecting to {country}")
        return False
    except Exception as e:
        logger.error(f"Error connecting to {country}: {e}")
        return False

def disconnect_nordvpn():
    """Disconnect from NordVPN - EC2 optimized."""
    try:
        logger.info("Disconnecting from NordVPN...")
        result = subprocess.run(['nordvpn', 'disconnect'], capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            logger.info("Successfully disconnected from NordVPN")
            time.sleep(5)
            return True
        else:
            logger.error(f"Error disconnecting from NordVPN: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        logger.error("Timeout disconnecting from NordVPN")
        return False
    except Exception as e:
        logger.error(f"Error disconnecting from NordVPN: {e}")
        return False

def get_current_ip():
    """Get current IP address - EC2 optimized."""
    try:
        # Try multiple IP services for reliability
        services = [
            "https://ipinfo.io/ip",
            "https://api.ipify.org",
            "https://checkip.amazonaws.com"
        ]

        for service in services:
            try:
                result = subprocess.run(["curl", "-s", "--max-time", "10", service],
                                      capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
            except:
                continue

        return "Unknown"
    except:
        return "Unknown"

def setup_ec2_chrome_driver():
    """Set up Chrome WebDriver optimized for EC2 using pip-only approach."""
    chrome_options = Options()

    # EC2-specific Chrome options for pip-only setup
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--remote-debugging-port=9222")
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
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-features=TranslateUI")
    chrome_options.add_argument("--disable-ipc-flooding-protection")

    # Memory optimization for EC2
    chrome_options.add_argument("--memory-pressure-off")
    chrome_options.add_argument("--max_old_space_size=4096")

    # Create unique temporary directory in /tmp for EC2
    unique_id = str(uuid.uuid4())[:8]
    timestamp = str(int(time.time()))
    temp_dir_name = f"ec2_chrome_session_{timestamp}_{unique_id}"
    temp_dir = os.path.join("/tmp", temp_dir_name)
    os.makedirs(temp_dir, exist_ok=True)
    chrome_options.add_argument(f"--user-data-dir={temp_dir}")

    # User agent
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # Exclude automation flags
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    # Prefs for clean session
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

    # Create WebDriver with pip-only approach
    try:
        # Try ChromeDriverManager first (pip-installed)
        logger.info("Attempting to use ChromeDriverManager (pip-installed)...")
        driver_path = ChromeDriverManager().install()
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.info("✅ Successfully using ChromeDriverManager")
    except Exception as e1:
        logger.warning(f"ChromeDriverManager failed: {e1}")
        try:
            # Try chromedriver-autoinstaller as backup
            logger.info("Attempting to use chromedriver-autoinstaller...")
            import chromedriver_autoinstaller
            chromedriver_autoinstaller.install()
            driver = webdriver.Chrome(options=chrome_options)
            logger.info("✅ Successfully using chromedriver-autoinstaller")
        except Exception as e2:
            logger.warning(f"chromedriver-autoinstaller failed: {e2}")
            try:
                # Final fallback - try system Chrome if available
                logger.info("Attempting to use system Chrome...")
                service = Service()  # Use default system path
                driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("✅ Successfully using system Chrome")
            except Exception as e3:
                logger.error(f"All Chrome setup methods failed: {e1}, {e2}, {e3}")
                raise Exception(f"Could not initialize Chrome WebDriver. Tried ChromeDriverManager, chromedriver-autoinstaller, and system Chrome. Last error: {e3}")

    # Remove webdriver properties
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    logger.info(f"Created EC2 Chrome session with temp directory: {temp_dir}")

    # Store temp_dir for cleanup
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

        # Hotel address
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

        # Price extraction with multiple selectors
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

        # Extract dates
        try:
            checkin_element = driver.find_element(By.CSS_SELECTOR, "[data-testid='date-display-field-start']")
            checkout_element = driver.find_element(By.CSS_SELECTOR, "[data-testid='date-display-field-end']")
            hotel_data['checkin_date'] = checkin_element.text.strip()
            hotel_data['checkout_date'] = checkout_element.text.strip()
        except:
            hotel_data['checkin_date'] = "Unknown"
            hotel_data['checkout_date'] = "Unknown"

        # Extract nights
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
        cleaned = re.sub(r'[^\d.,]', '', price_text)

        if ',' in cleaned and '.' in cleaned:
            cleaned = cleaned.replace(',', '')
        elif ',' in cleaned and len(cleaned.split(',')[-1]) == 3:
            cleaned = cleaned.replace(',', '')
        elif ',' in cleaned and len(cleaned.split(',')[-1]) <= 2:
            cleaned = cleaned.replace(',', '.')

        return float(cleaned)
    except:
        return None

def handle_booking_popups(driver):
    """Handle popups on Booking.com."""
    try:
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
    """Scrape hotel price for a specific country - EC2 optimized."""
    driver = setup_ec2_chrome_driver()

    try:
        logger.info(f"Scraping hotel for country: {country}")
        current_ip = get_current_ip()
        logger.info(f"Current IP: {current_ip}")

        # Navigate to hotel URL with longer timeout for EC2
        driver.set_page_load_timeout(60)
        driver.get(hotel_url)
        time.sleep(8)  # Longer wait for EC2

        # Handle popups
        handle_booking_popups(driver)

        # Wait for page load
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except TimeoutException:
            logger.warning("Timeout waiting for page to load")

        time.sleep(5)

        # Extract hotel data
        hotel_data = extract_hotel_info_and_price(driver)
        hotel_data['country'] = country
        hotel_data['scraped_at'] = datetime.now().isoformat()
        hotel_data['url'] = hotel_url
        hotel_data['ip_address'] = current_ip

        # Scroll to pricing section and take screenshot
        os.makedirs("screenshots", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
        screenshot_file = f"screenshots/hotel_{country}_{timestamp}.png"
        logger.info(f"Taking screenshot: {screenshot_file}")

        try:
            # Try to find and scroll to the availability/pricing section
            pricing_selectors = [
                "[data-testid='availability-calendar-date-picker']",  # Date picker section
                ".hprt-table",  # Room table
                ".hp_rt_rooms_table",  # Alternative room table
                ".availability",  # Availability section
                "[data-testid='property-section-prices']",  # Prices section
                ".bui-price-display",  # Price display
                ".hprt-occupancy-occupancy-info"  # Occupancy info
            ]

            pricing_element = None
            for selector in pricing_selectors:
                try:
                    pricing_element = driver.find_element(By.CSS_SELECTOR, selector)
                    if pricing_element:
                        logger.info(f"Found pricing section with selector: {selector}")
                        break
                except:
                    continue

            if pricing_element:
                # Scroll to the pricing section
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", pricing_element)
                time.sleep(3)  # Wait for scroll to complete
                logger.info("Scrolled to pricing section")
            else:
                # Fallback: scroll down to middle of page
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
                time.sleep(2)
                logger.info("Scrolled to middle of page as fallback")

        except Exception as e:
            logger.warning(f"Could not scroll to pricing section: {e}")
            # Continue with screenshot anyway

        driver.save_screenshot(screenshot_file)
        hotel_data['screenshot'] = screenshot_file
        hotel_data['screenshot_s3_url'] = None  # Will be set after VPN disconnect
        logger.info(f"Screenshot saved: {screenshot_file}")

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

        # Clean up temp directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.info(f"Cleaned up temp directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Could not clean up temp directory {temp_dir}: {e}")

def main():
    """Main function optimized for EC2."""
    logger.info("Starting EC2 multi-country hotel price scraper")

    # Hotel URL
    hotel_url = "https://www.booking.com/hotel/nz/goodview-serviced-apartment.html?aid=304142&label=gen173nr-10CAEoggI46AdIM1gEaD2IAQGYATO4AQfIAQzYAQPoAQH4AQGIAgGoAgG4As7u_scGwAIB0gIkYmRiODNhYmQtYTVlNy00OTljLThjZjgtNzg2OWJjMzU4ODBj2AIB4AIB&sid=161052f1d90c5a7f57b951c160f1fb7f&all_sr_blocks=218269713_273703546_0_0_0&checkin=2026-03-08&checkout=2026-03-22&dest_id=-1506909&dest_type=city&dist=0&group_adults=2&group_children=0&hapos=2&highlighted_blocks=218269713_273703546_0_0_0&hpos=2&matching_block_id=218269713_273703546_0_0_0&no_rooms=1&req_adults=2&req_children=0&room1=A%2CA&sb_price_type=total&sr_order=popularity&sr_pri_blocks=218269713_273703546_0_0_0__156889&srepoch=1761589637&srpvid=901281bb46be0113&type=total&ucfs=1&selected_currency=EUR"

    print("🚀 EC2 Multi-Country Hotel Price Scraper")
    print("========================================")

    # # Initialize RDS table
    # logger.info("Initializing RDS database table...")
    # if create_hotel_prices_table():
    #     logger.info("✅ RDS table ready")
    # else:
    #     logger.warning("⚠️  Could not initialize RDS table - data will only be saved to CSV/JSON")

    # Get NordVPN countries
    countries = get_nordvpn_countries()
    if not countries:
        logger.error("No NordVPN countries available")
        return

    # Run on all countries
    countries = countries
    logger.info(f"Processing {len(countries)} countries: {', '.join(countries)}")

    all_hotel_data = []
    successful_countries = []
    failed_countries = []

    # Disconnect from VPN first
    disconnect_nordvpn()

    # Process countries
    logger.info(f"Processing {len(countries)} countries: {countries}")

    for i, country in enumerate(countries, 1):
        logger.info(f"Processing country {i}/{len(countries)}: {country}")

        # Connect to VPN
        if not connect_to_nordvpn_country(country):
            logger.error(f"Failed to connect to {country}")
            failed_countries.append(country)
            continue

        try:
            # Scrape hotel data
            hotel_data = scrape_hotel_for_country(hotel_url, country)

            if hotel_data and hotel_data.get('raw_price') != 'No price found':
                all_hotel_data.append(hotel_data)
                successful_countries.append(country)
                logger.info(f"✅ Success for {country}")
            else:
                logger.warning(f"❌ No data for {country}")
                failed_countries.append(country)

        except Exception as e:
            logger.error(f"❌ Error for {country}: {e}")
            failed_countries.append(country)

        # Longer pause between countries on EC2
        if i < len(countries):
            time.sleep(10)

    # Final disconnect
    disconnect_nordvpn()

    # Upload all screenshots to S3 after VPN disconnect
    logger.info("Uploading screenshots to S3...")
    for data in all_hotel_data:
        if data.get('screenshot') and os.path.exists(data['screenshot']):
            s3_url = upload_screenshot_to_s3(data['screenshot'])
            data['screenshot_s3_url'] = s3_url

    # Insert all hotel data to DynamoDB in one call
    logger.info("Inserting hotel data into DynamoDB")
    if all_hotel_data:
        if insert_hotel_data_to_dynamodb(all_hotel_data):
            logger.info(f"💾 DynamoDB: Successfully inserted {len(all_hotel_data)} records")
        else:
            logger.error(f"💾 DynamoDB: Failed to insert {len(all_hotel_data)} records")
    else:
        logger.info("💾 DynamoDB: No data to insert")

    # # Insert data into RDS
    # logger.info("Inserting hotel data into RDS...")
    # rds_inserts_success = 0
    # rds_inserts_failed = 0
    # for data in all_hotel_data:
    #     if insert_hotel_data_to_rds(data):
    #         rds_inserts_success += 1
    #     else:
    #         rds_inserts_failed += 1

    # Save results
    if all_hotel_data:
        df = pd.DataFrame(all_hotel_data)

        os.makedirs("hotel_prices", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = f"hotel_prices/ec2_hotel_prices_{timestamp}.csv"
        json_file = f"hotel_prices/ec2_hotel_prices_{timestamp}.json"

        df.to_csv(csv_file, index=False)
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(all_hotel_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Results saved to {csv_file} and {json_file}")

        # Print summary
        print("\n" + "="*60)
        print("🏨 EC2 HOTEL PRICE SUMMARY")
        print("="*60)

        for data in all_hotel_data:
            print(f"\n🌍 {data['country']}: {data['raw_price']}")

        print(f"\n✅ Successful: {len(successful_countries)}")
        print(f"❌ Failed: {len(failed_countries)}")

        # Count S3 uploads
        s3_uploads = sum(1 for data in all_hotel_data if data.get('screenshot_s3_url'))
        print(f"📸 Screenshots uploaded to S3: {s3_uploads}/{len(all_hotel_data)}")

        if s3_uploads > 0:
            print(f"🗂️  S3 bucket: apartmentscreenshots/hotel-scraper/")

        # # RDS insert statistics
        # print(f"💾 RDS inserts: {rds_inserts_success} successful, {rds_inserts_failed} failed")
        # if rds_inserts_success > 0:
        #     print(f"🔗 Database: {RDS_HOST}/{RDS_DB_NAME}")

    else:
        logger.warning("No data collected")

if __name__ == "__main__":
    main()
