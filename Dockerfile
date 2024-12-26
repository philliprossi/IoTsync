FROM python:3.9-slim

# Install nginx and supervisor
RUN apt-get update && apt-get install -y \
    supervisor \
    nginx \
    curl \
    gettext-base \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/nginx/sites-enabled/default

# Create main nginx config
RUN echo 'user www-data;\n\
worker_processes 1;\n\
error_log /var/log/nginx/error.log warn;\n\
pid /var/run/nginx.pid;\n\
\n\
events {\n\
    worker_connections 1024;\n\
}\n\
\n\
http {\n\
    include /etc/nginx/mime.types;\n\
    default_type application/octet-stream;\n\
    sendfile on;\n\
    keepalive_timeout 65;\n\
    access_log /var/log/nginx/access.log;\n\
    include /etc/nginx/conf.d/*.conf;\n\
}' > /etc/nginx/nginx.conf

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
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf.template

# Create necessary directories and set permissions
RUN mkdir -p /var/log/supervisor /var/log/nginx /var/lib/nginx/body /var/run/nginx logs data && \
    touch /var/run/nginx.pid && \
    chown -R www-data:www-data /var/log/nginx /var/lib/nginx /var/run/nginx /usr/share/nginx/html /var/run/nginx.pid && \
    chmod -R 755 /var/log/nginx /var/lib/nginx /var/run/nginx /usr/share/nginx/html logs data && \
    chmod 644 /var/run/nginx.pid

# Copy supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create startup script
RUN echo '#!/bin/sh\n\
export API_PORT=${API_PORT:-8000}\n\
echo "Using API_PORT=$API_PORT"\n\
envsubst "\$API_PORT" < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf\n\
echo "Generated nginx configuration:"\n\
cat /etc/nginx/conf.d/default.conf\n\
echo "Testing nginx configuration..."\n\
nginx -t\n\
echo "Starting supervisor..."\n\
exec "$@"' > /docker-entrypoint.sh && \
    chmod +x /docker-entrypoint.sh

# Set entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisord.conf"] 