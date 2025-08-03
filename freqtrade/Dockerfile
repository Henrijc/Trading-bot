FROM python:3.11-slim

WORKDIR /freqtrade

# Install only essential system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install pip and setuptools
RUN pip install --upgrade pip setuptools

# Copy requirements and install base dependencies first
COPY freqtrade/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install freqtrade with --no-deps to avoid TA-Lib dependency
RUN pip install --no-deps freqtrade==2024.1

# Install missing freqtrade dependencies (without TA-Lib)
RUN pip install --no-cache-dir \
    aiofiles \
    ast-comments \
    freqtrade-client \
    janus \
    "python-telegram-bot>=20.1" \
    schedule \
    technical

# Copy application code
COPY freqtrade/ .

# Copy shared services from backend (CRITICAL FOR IMPORTS)
COPY backend/services ./services

# Set PYTHONPATH to find services
ENV PYTHONPATH="/freqtrade:/freqtrade/services:$PYTHONPATH"

# Create user_data directory
RUN mkdir -p /freqtrade/user_data/logs

# Expose port
EXPOSE 8082

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8082/health || exit 1

# Start the trading bot
CMD ["python", "luno_trading_bot.py"]