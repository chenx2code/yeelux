FROM python:3.11-slim

WORKDIR /app

# Install build dependencies required by python packages (like netifaces)
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc-dev && rm -rf /var/lib/apt/lists/*

# Install dependencies first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the Flask port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=web_app/app.py
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "web_app/app.py"]
