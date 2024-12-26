#!/bin/sh

# Replace environment variables in nginx config
envsubst '$API_PORT' < /etc/nginx/conf.d/nginx.template > /etc/nginx/conf.d/default.conf

# Start nginx
exec "$@" 