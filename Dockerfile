FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY input.py .
COPY fixed_plugin.py .
COPY test_harness.py .
COPY test_plugin.py .
COPY setup.sh .
COPY run.sh .
COPY test.sh .

# Make scripts executable
RUN chmod +x setup.sh run.sh test.sh

# Run setup and tests
RUN ./setup.sh

# Default command runs tests
CMD ["./test.sh"]


