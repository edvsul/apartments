# Hotel Price Scraper

A Python project for scraping hotel prices from Booking.com. This scraper can extract price information, hotel details, and booking dates from Booking.com hotel pages.

## Features

- 🏨 Extract hotel name, address, and rating
- 💰 Get current pricing information
- 📅 Extract check-in/check-out dates
- 🌙 Number of nights calculation
- 🤖 Handles anti-bot measures with Selenium
- 📝 Comprehensive logging
- 🛡️ Error handling and retry logic

## Installation

### Option 1: Automatic Setup (Recommended)

Run the setup script to automatically create a virtual environment and install dependencies:

```bash
chmod +x setup.sh
./setup.sh
```

### Option 2: Manual Setup

1. Create a virtual environment:
```bash
python3 -m venv venv
```

2. Activate the virtual environment:
```bash
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Activating the Environment

Before running the scraper, always activate the virtual environment:

```bash
source venv/bin/activate
```

When you're done, deactivate it:

```bash
deactivate
```

## Usage

### Basic Usage

```python
from hotel_scraper import BookingHotelScraper

# Create scraper instance
with BookingHotelScraper(headless=True) as scraper:
    result = scraper.scrape_hotel_price("https://www.booking.com/hotel/...")
    print(result)
```

### Run the Example

The project includes an example that scrapes the Goodview Serviced Apartment in New Zealand:

```bash
python example_usage.py
```

## Sample Output

```json
{
  "hotel_name": "Goodview Serviced Apartment",
  "address": "Auckland, New Zealand",
  "rating": "8.5",
  "raw_price": "NZ$2,356",
  "cleaned_price": 2356.0,
  "checkin_date": "Sat 8 Mar 2026",
  "checkout_date": "Sun 22 Mar 2026",
  "nights": "14 nights",
  "scraped_at": "2024-10-27T19:30:00.000000",
  "url": "https://www.booking.com/hotel/..."
}
```

## Requirements

- Python 3.7+
- Chrome browser (for Selenium WebDriver)
- Internet connection

## Notes

- The scraper uses Selenium with Chrome WebDriver for better compatibility with dynamic content
- Includes anti-detection measures to avoid being blocked
- Respects website's robots.txt and rate limiting
- For educational and personal use only

## Disclaimer

This tool is for educational purposes only. Please respect Booking.com's terms of service and use responsibly. Consider using official APIs when available for production use.
