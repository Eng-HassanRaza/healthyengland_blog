#!/bin/bash

# Auto Generate Content Script with Email Notifications
# Runs twice daily at 9:00 AM and 3:00 PM UK time

# Configuration
PROJECT_DIR="/var/www/healthyengland"
VENV_PATH="$PROJECT_DIR/venv/bin/activate"
LOG_FILE="/var/log/auto_generate.log"
ERROR_LOG="/var/log/auto_generate_errors.log"
EMAIL_TO="info@healthyengland.com"
EMAIL_FROM="noreply@healthyengland.com"

# Function to send email notification
send_email() {
    local subject="$1"
    local body="$2"
    local is_error="$3"
    
    if [ "$is_error" = "true" ]; then
        echo "ERROR: $body" >> "$ERROR_LOG"
        # Send email notification for errors
        echo "$body" | mail -s "$subject" -a "From: $EMAIL_FROM" "$EMAIL_TO" 2>/dev/null || echo "Failed to send email notification" >> "$ERROR_LOG"
    else
        echo "SUCCESS: $body" >> "$LOG_FILE"
    fi
}

# Function to log with timestamp
log_with_timestamp() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Start logging
log_with_timestamp "Starting auto content generation..."

# Change to project directory
cd "$PROJECT_DIR" || {
    send_email "Auto Generate Failed - Directory Error" "Failed to change to project directory: $PROJECT_DIR" "true"
    exit 1
}

# Activate virtual environment
source "$VENV_PATH" || {
    send_email "Auto Generate Failed - Virtual Environment Error" "Failed to activate virtual environment at: $VENV_PATH" "true"
    exit 1
}

# Check if Django is working
python manage.py check > /dev/null 2>&1 || {
    send_email "Auto Generate Failed - Django Check Error" "Django check failed. Please check the application status." "true"
    exit 1
}

# Run the auto generation command
log_with_timestamp "Executing auto_generate command..."
if python manage.py auto_generate >> "$LOG_FILE" 2>&1; then
    log_with_timestamp "Auto generation completed successfully"
    send_email "Auto Generate Success" "Content generation completed successfully at $(date)" "false"
else
    error_msg="Auto generation failed. Check logs at $ERROR_LOG"
    log_with_timestamp "Auto generation failed"
    send_email "Auto Generate Failed - Execution Error" "$error_msg" "true"
    exit 1
fi

# Check if any new content was created
NEW_POSTS=$(python manage.py shell -c "
from blog.models import Post
from django.utils import timezone
from datetime import timedelta
recent_posts = Post.objects.filter(created_at__gte=timezone.now() - timedelta(hours=1))
print(recent_posts.count())
" 2>/dev/null | tail -1)

# Ensure NEW_POSTS is a number
if ! [[ "$NEW_POSTS" =~ ^[0-9]+$ ]]; then
    NEW_POSTS=0
fi

if [ "$NEW_POSTS" -gt 0 ]; then
    log_with_timestamp "Successfully created $NEW_POSTS new posts"
    send_email "New Content Generated" "Successfully created $NEW_POSTS new blog posts at $(date)" "false"
else
    log_with_timestamp "No new posts were created"
fi

log_with_timestamp "Auto generation process completed"
