#!/bin/bash
# Simple cron runner for Render
# Run this via a separate Service (Background Worker) or Cron Job

echo "Starting Expiry Job..."
cd /app/backend
python3 -m app.jobs.expiry_worker
echo "Job Finished."
