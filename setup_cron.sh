#!/bin/bash

# Setup script to configure cron job for TikTok optimal posting times
# This script sets up automated content generation at peak TikTok engagement times

echo "Setting up TikTok-optimized cron job for content generation..."

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script with sudo or as root to configure cron jobs"
    echo "Usage: sudo ./setup_cron.sh"
    exit 1
fi

# Set timezone to US Eastern Time
echo "Setting system timezone to US Eastern Time..."
timedatectl set-timezone America/New_York

# Verify timezone change
echo "Current timezone: $(timedatectl show --property=Timezone --value)"
echo "Current time: $(date)"

# Install the cron job
echo "Installing cron job for TikTok optimal posting times..."
crontab /var/www/healthyengland/crontab_config.txt

# Verify cron job installation
echo "Verifying cron job installation..."
crontab -l

echo ""
echo "✅ Setup complete!"
echo "📅 Content will be generated automatically at:"
echo "   - 6:00 AM EST (Early morning peak)"
echo "   - 10:00 AM EST (Mid-morning break peak)"
echo "   - 7:00 PM EST (Evening peak)"
echo ""
echo "📊 These times are optimized for maximum TikTok engagement in the US"
echo "🕐 System timezone is now set to US Eastern Time"
echo ""
echo "To view cron jobs: crontab -l"
echo "To remove cron jobs: crontab -r"
