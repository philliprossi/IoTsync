FROM ubuntu:22.04

# Install Python and supervisor
RUN apt-get update && apt-get install -y \
    python3.9 \
    python3-pip \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks for python
RUN ln -s /usr/bin/python3 /usr/bin/python

# Install UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies using UV
RUN /root/.cargo/bin/uv pip install --no-cache -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /var/log/supervisor

# Set proper permissions
RUN chmod -R 755 /app/logs /app/data

# Copy supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Command to run supervisor
CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisord.conf"] 