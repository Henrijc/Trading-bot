FROM python:3.11-bullseye

WORKDIR /app # Set WORKDIR to the root of the copied application

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip to the latest version
RUN pip install --upgrade pip

# Install freqtrade with --no-deps to avoid TA-Lib dependency
RUN pip install --no-deps freqtrade==2024.1

# Copy freqtrade requirements.txt and install dependencies
# Note: This copies only freqtrade/requirements.txt relative to the build context
COPY freqtrade/requirements.txt ./freqtrade/requirements.txt
RUN pip install --no-cache-dir -r ./freqtrade/requirements.txt

# Copy the entire project repository into /app
# This is the key change to ensure all files are present
COPY . /app

# Set PYTHONPATH to include the /app root
ENV PYTHONPATH="/app:$PYTHONPATH"

# Create user_data directory (now relative to /app/freqtrade)
RUN mkdir -p /app/freqtrade/user_data/logs

# Expose port
EXPOSE 8082

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
CMD curl -f http://localhost:8082/api/v1/ping || exit 1

# Start the trading bot with the CORRECT filename
# Path is now relative to /app, which contains /app/freqtrade
CMD ["python", "freqtrade/luno_trading_bot.py"]