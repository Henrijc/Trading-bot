FROM python:3.11-bullseye

WORKDIR /app # Set WORKDIR to the root of the copied application

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements.txt and install dependencies
# Note: This copies only backend/requirements.txt relative to the build context
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy the entire project repository into /app
# This is the key change to ensure all files are present
COPY . /app

# Ensure directories are explicitly created for writing, if not using external volumes for them
# These paths are relative to /app
RUN mkdir -p /app/backend/logs
RUN mkdir -p /app/backend/historical_data
RUN chmod 755 /app/backend/logs /app/backend/historical_data

# Set PYTHONPATH to include the /app root
ENV PYTHONPATH="/app:$PYTHONPATH"

# Expose the port the application listens on
EXPOSE 8001

# Command to run the application (assuming server.py is in /app/backend)
CMD ["python", "-m", "uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "8001"]