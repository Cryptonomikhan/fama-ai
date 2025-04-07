FROM python:3.10-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="${PYTHONPATH}:/app"

# Install system dependencies needed for Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    build-essential \
    libpq-dev \
    python3-dev \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Install critical dependencies first to prevent compatibility issues
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir six>=1.16.0 mcp>=0.1.0

# Install Python dependencies separately to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directories for temporary files and ensure they exist
RUN mkdir -p /app/uploads /app/logs /app/data /app/knowledge

# Copy application code
COPY . .

# Create non-root user for security
RUN groupadd -r fama && \
    useradd -r -g fama -d /app -s /bin/bash fama && \
    chown -R fama:fama /app && \
    chmod -R 755 /app/uploads /app/logs /app/data /app/knowledge

# Switch to non-root user
USER fama

# Expose the application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set up entry point and command to start the FastAPI server
ENTRYPOINT ["python", "-m"]
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
