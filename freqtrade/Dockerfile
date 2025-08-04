FROM python:3.11-bullseye

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    wget \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Install freqtrade with --no-deps to avoid TA-Lib dependency
RUN pip install --no-deps freqtrade==2024.1

# Copy freqtrade requirements.txt and install dependencies
COPY freqtrade/requirements.txt ./freqtrade/requirements.txt
RUN pip install --no-cache-dir -r ./freqtrade/requirements.txt

# Install additional dependencies required by shared services (like luno_service)
# This includes 'aiohttp' which was previously missing
RUN pip install --no-cache-dir \
    aiohttp

# Copy the entire project repository into /app
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

# Start the trading bot
CMD ["python", "/app/freqtrade/luno_trading_bot.py"]