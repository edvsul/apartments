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

## AWS Architecture

This project is designed to run on AWS infrastructure with the following components:

### Architecture Diagram

<img width="3713" height="2588" alt="image" src="https://github.com/user-attachments/assets/c5a6ca09-629d-42cd-be5f-97800c843db4" />


**Architecture Overview:**
- **VPC (10.0.0.0/16)** with public and private subnets in Availability Zone A
- **Public Subnet (10.0.1.0/24)** contains the EC2 instance with public IP
- **Private Subnet (10.0.2.0/24)** contains the RDS MySQL database
- **Amazon EC2** instance running the hotel scraper application
- **Amazon IAM** role for EC2 instance with inline policies to connect to RDS and S3. SSM and CloudWatch included.
- **Amazon RDS** MySQL database where records about hotel is saved
- **Amazon S3** bucket for screenshot storage
- **Amazon CloudWatch** for collecting logs from EC2 instance under /var/log/hotel_scraper.log
- **Systems Manager** for secure access to EC2 instance
- **Internet Gateway** for external connectivity to Booking.com and other services

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

### Multi-Country Price Comparison

For advanced users with NordVPN, you can compare hotel prices across different countries:

```bash
./run_multi_country_scraper.sh
```

**Requirements for Multi-Country Scraping:**
- NordVPN subscription and CLI installed
- Must be logged into NordVPN (`nordvpn login`)
- Stable internet connection

This will:
- Connect to multiple countries via NordVPN
- Scrape the same hotel from each location
- Compare pricing differences by region
- Generate CSV and JSON reports
- Take screenshots for verification

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
