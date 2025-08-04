FROM python:3.11-bullseye

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements.txt and install dependencies
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r ./requirements.txt

# Copy the backend code
COPY . .

# Copy the shared services from parent directory 
COPY ../backend/services ./services

# Ensure directories are explicitly created for writing
RUN mkdir -p /app/logs
RUN mkdir -p /app/historical_data
RUN chmod 755 /app/logs /app/historical_data

# Expose the port
EXPOSE 8001

# Command to run the application
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]