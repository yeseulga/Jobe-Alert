FROM python:3.11-slim

# Prevent Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1


# Install system dependencies for Tesseract OCR, Playwright, and others
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-kor \
    tesseract-ocr-eng \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file first to cache packages in Docker layers
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and chromium browser with system dependencies
RUN pip install --no-cache-dir playwright && playwright install --with-deps chromium

# Copy the rest of the application code
COPY . .

# Set default command to run the main script
CMD ["python", "main.py"]
