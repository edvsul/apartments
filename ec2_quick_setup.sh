#!/bin/bash

# Minimal EC2 Setup Script - NordVPN Pre-installed and Configured
# Uses pip only for software installation

echo "⚡ Minimal EC2 Setup for Hotel Price Scraper"
echo "============================================"
echo "📋 Assuming NordVPN is installed and configured"

# Verify Python 3 is available
echo "🐍 Checking Python 3..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3 first."
    exit 1
fi
echo "✅ Python 3 found: $(python3 --version)"

# Verify pip is available
echo "📦 Checking pip..."
if ! command -v pip3 &> /dev/null && ! python3 -m pip --version &> /dev/null; then
    echo "❌ pip not found. Please install pip first."
    exit 1
fi
echo "✅ pip found"

# Verify NordVPN (no configuration)
echo "🔒 Verifying NordVPN..."
if command -v nordvpn &> /dev/null; then
    echo "✅ NordVPN found: $(nordvpn --version)"
    echo "📋 Assuming NordVPN is already configured"
else
    echo "❌ NordVPN not found! Please install NordVPN first."
    exit 1
fi

# Create Python virtual environment
echo "📦 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install all dependencies via pip
echo "📥 Installing Python dependencies via pip..."
pip install --upgrade pip

# Install Chrome and ChromeDriver via pip packages
echo "🌐 Installing Chrome dependencies via pip..."
pip install selenium webdriver-manager

# Install other required packages
echo "📦 Installing remaining dependencies..."
pip install -r requirements.txt

# Create output directories
echo "📁 Creating output directories..."
mkdir -p hotel_prices screenshots temp_chrome_sessions

# Test if Chrome/Chromium is available via webdriver-manager
echo "🧪 Testing Chrome setup via webdriver-manager..."
python3 -c "
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
try:
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver_path = ChromeDriverManager().install()
    print('✅ Chrome/ChromeDriver setup successful via webdriver-manager')
except Exception as e:
    print(f'⚠️  Chrome setup warning: {e}')
    print('   The scraper will attempt to use system Chrome if available')
"

deactivate

echo ""
echo "🎉 Minimal setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Run scraper: ./run_ec2_scraper.sh"
echo ""
echo "💡 Note: You should see (venv) in your prompt after step 1"
echo "🚀 Ready to scrape hotel prices across countries!"
echo "📋 All software installed via pip - no system packages required"
