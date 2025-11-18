FROM alpine:latest

# Install cron, curl, and bash
RUN apk add --no-cache dcron curl bash

# Create necessary directories
RUN mkdir -p /var/log/cron
RUN touch /var/log/cron/cron.log
RUN chmod 666 /var/log/cron/cron.log

# Create cron directory
RUN mkdir -p /etc/cron.d/

# Copy crontab files
COPY crontab.dev /etc/cron.d/crontab.dev
COPY crontab.prod /etc/cron.d/crontab.prod

# Copy job script
COPY run_job.sh /usr/local/bin/run_job.sh

# Give execution permission to files
RUN chmod 0644 /etc/cron.d/crontab.dev
RUN chmod 0644 /etc/cron.d/crontab.prod
RUN chmod +x /usr/local/bin/run_job.sh

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh

RUN dos2unix /entrypoint.sh

RUN chmod +x /entrypoint.sh

# Run the command on container startup
ENTRYPOINT ["/entrypoint.sh"]