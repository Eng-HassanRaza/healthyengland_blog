#!/bin/bash

# Automation Monitoring Script
# Use this to check the status of your automated content generation

echo "🤖 AUTOMATION MONITORING DASHBOARD"
echo "=================================="
echo ""

# Check timezone
echo "📍 Timezone: $(timedatectl show --property=Timezone --value)"
echo "🕐 Current Time: $(date)"
echo ""

# Check cron jobs
echo "⏰ CRON JOBS STATUS:"
echo "-------------------"
sudo crontab -l | grep auto_generate || echo "No automation cron jobs found"
echo ""

# Check recent logs
echo "📊 RECENT ACTIVITY (Last 10 entries):"
echo "--------------------------------------"
tail -10 /var/log/auto_generate.log 2>/dev/null || echo "No log entries found"
echo ""

# Check for errors
echo "❌ ERRORS (Last 5 entries):"
echo "---------------------------"
tail -5 /var/log/auto_generate_errors.log 2>/dev/null || echo "No errors found"
echo ""

# Check recent blog posts
echo "📝 RECENT BLOG POSTS (Last 5):"
echo "-------------------------------"
cd /var/www/healthyengland && source venv/bin/activate && python manage.py shell -c "
from blog.models import Post
from django.utils import timezone
from datetime import timedelta
recent_posts = Post.objects.filter(created_at__gte=timezone.now() - timedelta(days=1)).order_by('-created_at')[:5]
for post in recent_posts:
    print(f'  • {post.title} ({post.created_at.strftime(\"%Y-%m-%d %H:%M\")})')
" 2>/dev/null || echo "Could not fetch recent posts"
echo ""

# Check system resources
echo "💻 SYSTEM STATUS:"
echo "-----------------"
echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "Memory Usage: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')"
echo "Disk Usage: $(df -h / | awk 'NR==2{printf "%s", $5}')"
echo ""

echo "✅ Automation monitoring complete!"
