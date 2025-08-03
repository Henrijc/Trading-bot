FROM python:3.11-slim

WORKDIR /freqtrade

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY freqtrade/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY freqtrade/ .

# Create user_data directory
RUN mkdir -p /freqtrade/user_data/logs

# Expose port
EXPOSE 8082

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8082/api/v1/ping || exit 1

# Start the trading bot
CMD ["python", "luno_trading_bot.py"]