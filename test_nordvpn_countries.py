#!/usr/bin/env python3
"""
Quick test script to show the first 2 NordVPN countries that will be tested
"""

import subprocess
import sys

def get_nordvpn_countries():
    """Get list of available NordVPN countries."""
    try:
        print("🔍 Getting available NordVPN countries...")
        
        # Check if NordVPN is available
        result = subprocess.run(['nordvpn', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ NordVPN not found or not working")
            return []
        
        print(f"✅ NordVPN found: {result.stdout.strip()}")
        
        # Get countries
        result = subprocess.run(['nordvpn', 'countries'], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            countries_text = result.stdout.strip()
            print(f"📋 Raw NordVPN output: {countries_text[:200]}...")
            
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
            
            return unique_countries
        else:
            print(f"❌ Error getting NordVPN countries: {result.stderr}")
            return []
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout getting NordVPN countries")
        return []
    except Exception as e:
        print(f"❌ Error getting NordVPN countries: {e}")
        return []

def main():
    print("🧪 NordVPN Countries Test")
    print("=" * 40)
    
    countries = get_nordvpn_countries()
    
    if not countries:
        print("❌ No countries found. Please check NordVPN installation.")
        sys.exit(1)
    
    print(f"\n✅ Found {len(countries)} total countries")
    print(f"📋 All countries: {', '.join(countries[:10])}{'...' if len(countries) > 10 else ''}")
    
    # Show first 2 countries that will be tested
    test_countries = countries[:2]
    print(f"\n🎯 Countries that will be tested (first 2):")
    for i, country in enumerate(test_countries, 1):
        print(f"   {i}. {country}")
    
    print(f"\n⏱️  Estimated test time: {len(test_countries) * 2.5:.1f} minutes")
    print(f"🚀 Ready to run: ./run_ec2_scraper.sh")

if __name__ == "__main__":
    main()
