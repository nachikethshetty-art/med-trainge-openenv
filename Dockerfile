FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Create non-root user (required by HF Spaces)
RUN useradd -m -u 1000 user

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
COPY app_server.py .
COPY README.md .

# Set permissions
RUN chown -R user:user /app

# Switch to non-root user
USER user

# HF Spaces requires app to listen on port 7860
EXPOSE 7860

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=7860
ENV GROQ_API_KEY=""
ENV GEMINI_API_KEY=""

# Start the Flask app server
CMD ["python", "app_server.py"]

# Default command
CMD ["/bin/bash"]
