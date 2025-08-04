FROM python:3.11-bullseye

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl wget git build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all freqtrade code
COPY . .

# Create directories
RUN mkdir -p user_data/logs

EXPOSE 8082

CMD ["python", "luno_trading_bot.py"]