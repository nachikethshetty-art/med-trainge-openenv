FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY env.py .
COPY inference.py .
COPY openenv.yaml .
COPY README.md .

# Expose API port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV API_BASE_URL="https://api.openai.com/v1"
ENV MODEL_NAME="gpt-4"

# Default command
CMD ["/bin/bash"]
