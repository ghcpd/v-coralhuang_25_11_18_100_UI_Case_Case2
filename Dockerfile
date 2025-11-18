# Dockerfile for SD Upscale Plugin Testing
# This container builds a reproducible environment and runs the test suite

FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY input.py /app/
COPY fixed_plugin.py /app/
COPY test_plugin.py /app/
COPY setup.sh /app/
COPY test.sh /app/
COPY run.sh /app/

# Make scripts executable
RUN chmod +x /app/setup.sh /app/test.sh /app/run.sh

# Install Python dependencies
RUN /app/setup.sh

# Set default command to run tests
CMD ["/app/test.sh"]

# Alternative: To run interactive harness, use:
# docker run -it <image> /app/run.sh
