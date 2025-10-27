#!/usr/bin/env python3
"""
Example usage of the Booking.com hotel scraper
"""

from hotel_scraper import BookingHotelScraper
import json

def main():
    # The specific hotel URL you provided
    hotel_url = "https://www.booking.com/hotel/nz/goodview-serviced-apartment.html?aid=304142&label=gen173nr-10CAEoggI46AdIM1gEaD2IAQGYATO4AQfIAQzYAQPoAQH4AQGIAgGoAgG4As7u_scGwAIB0gIkYmRiODNhYmQtYTVlNy00OThjLThjZjgtNzg2OWJjMzU4ODBj2AIB4AIB&sid=161052f1d90c5a7f57b951c160f1fb7f&all_sr_blocks=218269713_273703546_0_0_0&checkin=2026-03-08&checkout=2026-03-22&dest_id=-1506909&dest_type=city&dist=0&group_adults=2&group_children=0&hapos=2&highlighted_blocks=218269713_273703546_0_0_0&hpos=2&matching_block_id=218269713_273703546_0_0_0&no_rooms=1&req_adults=2&req_children=0&room1=A%2CA&sb_price_type=total&sr_order=popularity&sr_pri_blocks=218269713_273703546_0_0_0__156889&srepoch=1761589637&srpvid=901281bb46be0113&type=total&ucfs=1&"
    
    print("🏨 Starting hotel price scraper...")
    print(f"📍 Target hotel: Goodview Serviced Apartment, New Zealand")
    print(f"📅 Check-in: 2026-03-08")
    print(f"📅 Check-out: 2026-03-22")
    print(f"👥 Guests: 2 adults")
    print("-" * 60)
    
    # Use the scraper with context manager for automatic cleanup
    with BookingHotelScraper(headless=True) as scraper:
        result = scraper.scrape_hotel_price(hotel_url)
        
        # Display results
        if 'error' in result:
            print(f"❌ Error occurred: {result['error']}")
        else:
            print("✅ Successfully scraped hotel information:")
            print(f"🏨 Hotel Name: {result.get('hotel_name', 'N/A')}")
            print(f"📍 Address: {result.get('address', 'N/A')}")
            print(f"⭐ Rating: {result.get('rating', 'N/A')}")
            print(f"💰 Price: {result.get('raw_price', 'N/A')}")
            if result.get('cleaned_price'):
                print(f"💵 Cleaned Price: ${result['cleaned_price']:.2f}")
            print(f"📅 Check-in: {result.get('checkin_date', 'N/A')}")
            print(f"📅 Check-out: {result.get('checkout_date', 'N/A')}")
            print(f"🌙 Nights: {result.get('nights', 'N/A')}")
            print(f"🕐 Scraped at: {result.get('scraped_at', 'N/A')}")
        
        print("-" * 60)
        print("📄 Full JSON result:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
