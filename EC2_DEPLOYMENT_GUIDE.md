# EC2 Deployment Guide for Hotel Price Scraper

## 🚀 Quick Start on Amazon Linux EC2

### Prerequisites
- EC2 instance running Amazon Linux 2 or Amazon Linux 2023
- Minimum recommended: **t3.medium** (2 vCPU, 4GB RAM)
- NordVPN subscription
- SSH access to your EC2 instance

### Step 1: Initial EC2 Setup

```bash
# Connect to your EC2 instance
ssh -i your-key.pem ec2-user@your-ec2-ip

# Clone or upload your project
git clone <your-repo> || scp -r apartments/ ec2-user@your-ec2-ip:~/

# Navigate to project directory
cd apartments/
```

### Step 2: Run EC2 Setup Script

Since NordVPN is already installed, you can use the quick setup:

```bash
# Make scripts executable
chmod +x ec2_quick_setup.sh run_ec2_scraper.sh

# Run the quick setup (NordVPN already installed)
./ec2_quick_setup.sh
```

Or use the full setup script:
```bash
chmod +x ec2_setup.sh
./ec2_setup.sh
```

This will:
- ✅ Update system packages
- ✅ Install Python 3 and development tools
- ✅ Install Google Chrome and dependencies
- ✅ Verify NordVPN installation and configure daemon
- ✅ Create Python virtual environment
- ✅ Install all Python dependencies
- ✅ Configure Chrome for headless operation

### Step 3: Configure NordVPN

```bash
# Login to NordVPN (required)
nordvpn login

# Verify login
nordvpn account

# Test connection
nordvpn connect United_States
nordvpn status
nordvpn disconnect
```

### Step 4: Run the Scraper

```bash
# Run the EC2-optimized scraper
./run_ec2_scraper.sh
```

## 🔧 EC2-Specific Optimizations

### Key Differences from Local Version

1. **Memory Management**
   - Uses `/tmp` for Chrome temp directories
   - Implements memory pressure controls
   - Limits to 5 countries (vs 10 locally)

2. **Chrome Configuration**
   - Optimized for headless EC2 environment
   - Additional stability flags
   - Better resource management

3. **Network Handling**
   - Longer timeouts for VPN connections
   - Multiple IP detection services
   - Enhanced error handling

4. **Logging**
   - Comprehensive logging to `hotel_scraper.log`
   - EC2 instance detection and reporting
   - Resource usage monitoring

### File Structure on EC2

```
/home/ec2-user/apartments/
├── multi_country_hotel_scraper_ec2.py  # EC2-optimized scraper
├── ec2_setup.sh                        # EC2 setup script
├── run_ec2_scraper.sh                  # EC2 run script
├── hotel_scraper.log                   # Execution logs
├── hotel_prices/                       # CSV/JSON results
├── screenshots/                        # Visual evidence
└── venv/                              # Python virtual environment
```

## 📊 Expected Performance on EC2

### Instance Type Recommendations

| Instance Type | vCPU | RAM | Recommended Use |
|---------------|------|-----|-----------------|
| t3.small      | 2    | 2GB | Testing only    |
| t3.medium     | 2    | 4GB | **Recommended** |
| t3.large      | 2    | 8GB | Heavy usage     |

### Timing Estimates

- **Setup**: 5-10 minutes
- **Per Country**: 2-3 minutes
- **Total (5 countries)**: 15-20 minutes

## 🛠️ Troubleshooting

### Common Issues

1. **Chrome Installation Failed**
   ```bash
   # Manual Chrome installation
   cd /tmp
   wget https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
   sudo yum localinstall -y google-chrome-stable_current_x86_64.rpm
   ```

2. **NordVPN Connection Issues**
   ```bash
   # Restart NordVPN daemon
   sudo systemctl restart nordvpnd
   sudo systemctl status nordvpnd
   
   # Check login status
   nordvpn logout
   nordvpn login
   ```

3. **Memory Issues**
   ```bash
   # Check memory usage
   free -h
   
   # Clear cache if needed
   sudo sync && sudo sysctl vm.drop_caches=3
   ```

4. **Chrome Process Hanging**
   ```bash
   # Kill Chrome processes
   pkill -f chrome
   
   # Clear temp directories
   rm -rf /tmp/ec2_chrome_session_*
   ```

### Log Analysis

```bash
# View real-time logs
tail -f hotel_scraper.log

# Check for errors
grep -i error hotel_scraper.log

# Check successful countries
grep -i "successfully scraped" hotel_scraper.log
```

## 🔒 Security Considerations

### EC2 Security Group
Ensure your security group allows:
- **SSH (22)**: For access
- **HTTPS (443)**: For web scraping
- **HTTP (80)**: For some services

### NordVPN Security
- Store credentials securely
- Use IAM roles instead of hardcoded credentials
- Consider using AWS Secrets Manager for NordVPN credentials

## 📈 Monitoring and Scaling

### CloudWatch Metrics
Monitor:
- CPU utilization
- Memory usage
- Network I/O
- Disk space

### Auto-scaling Considerations
- Use spot instances for cost savings
- Consider Lambda for scheduled runs
- Use S3 for result storage

## 💰 Cost Optimization

### Estimated Costs (us-east-1)
- **t3.medium**: ~$0.0416/hour
- **Data transfer**: Minimal for scraping
- **Storage**: ~$0.10/GB/month

### Cost-saving Tips
1. Use spot instances (up to 90% savings)
2. Stop instance when not in use
3. Use smaller instance for testing
4. Store results in S3, not EBS

## 🔄 Automation

### Cron Job Example
```bash
# Run daily at 2 AM UTC
0 2 * * * /home/ec2-user/apartments/run_ec2_scraper.sh >> /home/ec2-user/scraper_cron.log 2>&1
```

### Lambda Integration
Consider using AWS Lambda for:
- Scheduled execution
- Result processing
- Notification sending

## 📞 Support

If you encounter issues:
1. Check `hotel_scraper.log` for detailed errors
2. Verify all prerequisites are installed
3. Test NordVPN connection manually
4. Ensure sufficient EC2 resources

The EC2 version is optimized for cloud deployment with enhanced stability, logging, and resource management compared to the local version.
