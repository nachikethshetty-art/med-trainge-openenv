FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=7860 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app:$PYTHONPATH

# Install system dependencies with retry
RUN apt-get update --allow-unauthenticated && \
    apt-get install -y --no-install-recommends \
    git \
    curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user (HF Spaces requirement)
RUN useradd -m -u 1000 user

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY --chown=user:user requirements.txt pyproject.toml* ./

# Install Python dependencies with pip cache disabled
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=user:user . .

# Switch to non-root user
USER user

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Expose port
EXPOSE 7860

# Start the Flask application
CMD ["python", "app_server.py"]
