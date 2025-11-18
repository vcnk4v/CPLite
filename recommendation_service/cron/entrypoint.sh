#!/bin/sh

# Create necessary directories
mkdir -p /var/log/cron
touch /var/log/cron/cron.log
chmod 666 /var/log/cron/cron.log

# Set proper permissions for the script
chmod +x /usr/local/bin/run_job.sh

# Select crontab based on environment
if [ "$ENVIRONMENT" = "production" ]; then
    echo "Using production crontab"
    cp /etc/cron.d/crontab.prod /etc/crontabs/root
else
    echo "Using development crontab"
    cp /etc/cron.d/crontab.dev /etc/crontabs/root
fi

# Set proper permissions on the crontab
chmod 0644 /etc/crontabs/root

echo "Cron configuration:"
cat /etc/crontabs/root

echo "Starting cron service..."
# Run crond in foreground with debug level 8
crond -f -d 8