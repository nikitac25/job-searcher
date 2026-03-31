#!/bin/bash
# Ensure the Flask vacancy server is running
# Called by cron daily at 2:53

cd /home/den/job-search
[ -f /home/den/job-search/.env ] && export $(grep -v '^#' /home/den/job-search/.env | xargs)
LOG=/home/den/job-search/app.log

# Check if server actually responds, not just if process exists
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:8080/ 2>/dev/null)

if [ "$HTTP_CODE" = "200" ]; then
    echo "[$(date)] Server is responding (HTTP $HTTP_CODE), OK" >> "$LOG"
else
    echo "[$(date)] Server not responding (HTTP $HTTP_CODE), restarting..." >> "$LOG"
    # Kill any zombie processes holding the port
    lsof -ti:8080 | xargs kill -9 2>/dev/null
    sleep 1
    nohup python3 app.py >> "$LOG" 2>&1 &
    sleep 2
    # Verify restart
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:8080/ 2>/dev/null)
    echo "[$(date)] Restart result: HTTP $HTTP_CODE" >> "$LOG"
fi
