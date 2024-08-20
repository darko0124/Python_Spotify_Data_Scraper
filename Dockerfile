FROM python:3.10-slim

# Set the working directory
WORKDIR /usr/src/app

# Copy application files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install cron
RUN apt-get update && apt-get install -y cron

# Copy crontab file and set permissions
COPY crontab /etc/cron.d/my-cron-job
RUN chmod 0644 /etc/cron.d/my-cron-job

# Apply cron job
RUN crontab /etc/cron.d/my-cron-job

# Create the log file that cron will write to
RUN touch /var/log/cron.log

# Copy credentials (if needed)
COPY spotify_credentials.json /usr/src/spotify_credentials.json
COPY G_Drive_Credentials.json /usr/src/G_Drive_Credentials.json

# Label for metadata
LABEL authors="darko"

# Run cron and keep the container running
CMD ["cron", "-f"]
