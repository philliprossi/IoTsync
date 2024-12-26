FROM python:3.9-slim

# Install nginx and supervisor
RUN apt-get update && apt-get install -y \
    supervisor \
    nginx \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/nginx/sites-enabled/default

# Install UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh || \
    (sleep 2 && curl -LsSf https://astral.sh/uv/install.sh | sh) || \
    (sleep 5 && curl -LsSf https://astral.sh/uv/install.sh | sh)

# Add UV to PATH
ENV PATH="/root/.local/bin:${PATH}"

# Set working directory
WORKDIR /app
ENV PYTHONPATH=/app/backend

# Copy requirements first to leverage Docker cache
COPY backend/requirements.txt backend/
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r backend/requirements.txt || \
    (sleep 2 && pip install -r backend/requirements.txt) || \
    (sleep 5 && pip install -r backend/requirements.txt)

# Copy backend code
COPY backend/ backend/

# Copy frontend files
COPY frontend/src /usr/share/nginx/html

# Copy nginx configuration
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Create necessary directories and set permissions
RUN mkdir -p /var/log/supervisor /var/log/nginx /var/lib/nginx/body /var/run/nginx logs data && \
    touch /var/run/nginx.pid && \
    chown -R root:root /var/log/nginx /var/lib/nginx /var/run/nginx /usr/share/nginx/html /var/run/nginx.pid && \
    chmod -R 755 /var/log/nginx /var/lib/nginx /var/run/nginx /usr/share/nginx/html logs data && \
    chmod 644 /var/run/nginx.pid

# Copy supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Command to run supervisor
CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisord.conf"] 