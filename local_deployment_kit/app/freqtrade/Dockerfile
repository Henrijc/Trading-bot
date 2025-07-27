# Freqtrade Trading Bot Dockerfile
FROM python:3.11-slim

WORKDIR /freqtrade

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install TA-Lib (required for technical analysis)
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib/ && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd .. && \
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /freqtrade/user_data/models
RUN mkdir -p /freqtrade/user_data/logs
RUN mkdir -p /freqtrade/logs

# Expose port for API
EXPOSE 8082

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8082/api/v1/ping || exit 1

# Default command (can be overridden)
CMD ["python3", "luno_trading_bot.py", "--config", "config.json"]