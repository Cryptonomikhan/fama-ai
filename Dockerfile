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
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Install critical dependencies first to prevent compatibility issues
RUN pip install --no-cache-dir --upgrade pip six>=1.16.0 setuptools wheel

# Install Python dependencies separately to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directories for temporary files
RUN mkdir -p /app/uploads /app/logs /app/data

# Copy application code
COPY . .

# Create non-root user for security
RUN groupadd -r fama && \
    useradd -r -g fama -d /app -s /bin/bash fama && \
    chown -R fama:fama /app

# Switch to non-root user
USER fama

# Expose the application port
EXPOSE 8000

# Set up entry point and command to start the FastAPI server
ENTRYPOINT ["python", "-m"]
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
