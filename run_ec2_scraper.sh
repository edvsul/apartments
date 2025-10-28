#!/bin/bash

# EC2-optimized script to run the multi-country hotel scraper

echo "🚀 EC2 Multi-Country Hotel Price Scraper"
echo "========================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./ec2_setup.sh first."
    exit 1
fi

# Check if NordVPN is installed and running
if ! command -v nordvpn &> /dev/null; then
    echo "❌ NordVPN not found. Please run ./ec2_setup.sh first."
    exit 1
fi

# Check NordVPN daemon
if ! systemctl is-active --quiet nordvpnd; then
    echo "🔧 Starting NordVPN daemon..."
    sudo systemctl start nordvpnd
    sleep 5
fi

# Check NordVPN login status
if nordvpn account 2>&1 | grep -q "You are not logged in"; then
    echo "❌ Not logged into NordVPN. Please login first:"
    echo "   nordvpn login"
    exit 1
fi

echo "✅ NordVPN check passed"

# Check Chrome installation
if ! command -v google-chrome &> /dev/null; then
    echo "❌ Google Chrome not found. Please run ./ec2_setup.sh first."
    exit 1
fi

# Test Chrome headless
if ! google-chrome --headless --disable-gpu --no-sandbox --dump-dom https://www.google.com > /dev/null 2>&1; then
    echo "⚠️  Chrome headless test failed, but continuing..."
else
    echo "✅ Chrome headless test passed"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check Python dependencies
echo "📦 Checking Python dependencies..."
python -c "import pandas, selenium, requests" 2>/dev/null || {
    echo "❌ Missing Python dependencies. Installing..."
    pip install -r requirements.txt
}

# Create output directories
mkdir -p hotel_prices screenshots temp_chrome_sessions

# Set environment variables for EC2
export DISPLAY=:99
export CHROME_BIN=/usr/bin/google-chrome
export CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Clean up any existing Chrome processes
pkill -f chrome > /dev/null 2>&1 || true

# Set resource limits for EC2
ulimit -n 4096  # Increase file descriptor limit

# Run the EC2-optimized scraper
echo "🚀 Starting EC2 hotel scraper..."
echo "🧪 This will test hotel prices across 2 countries (testing mode)"
echo "⏱️  Estimated time: 5-8 minutes"
echo "📊 Logs will be saved to hotel_scraper.log"
echo ""

# Run with timeout to prevent hanging
timeout 1800 python -u multi_country_hotel_scraper_ec2.py > /var/log/flights_scraper_script.log

EXIT_CODE=$?

if [ $EXIT_CODE -eq 124 ]; then
    echo "⚠️  Scraper timed out after 30 minutes"
elif [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Scraper completed successfully"
else
    echo "❌ Scraper exited with error code: $EXIT_CODE"
fi

# Clean up Chrome processes
pkill -f chrome > /dev/null 2>&1 || true

# Clean up temp directories
find /tmp -name "ec2_chrome_session_*" -type d -mmin +60 -exec rm -rf {} + 2>/dev/null || true

# Deactivate virtual environment
deactivate

echo ""
echo "📊 Check results in:"
echo "   - hotel_prices/ directory for CSV/JSON files"
echo "   - screenshots/ directory for visual evidence"
echo "   - hotel_scraper.log for detailed logs"
echo ""

# Show disk usage
echo "💾 Disk usage after scraping:"
du -sh hotel_prices/ screenshots/ 2>/dev/null || echo "   No output directories found"

# Disconnect from VPN
echo "🔌 Disconnecting from VPN..."
nordvpn disconnect > /dev/null 2>&1 || true

echo "✅ EC2 scraping session completed!"
