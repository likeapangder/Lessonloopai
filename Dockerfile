FROM python:3.10-slim

# Install ffmpeg for audio compression
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependencies first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY backend/ ./backend/

# Expose the port Render provides (or default 5000)
ENV PORT=5000
EXPOSE $PORT

# Run gunicorn from the backend directory
WORKDIR /app/backend
CMD gunicorn app:app --bind 0.0.0.0:$PORT
