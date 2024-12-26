#!/bin/sh

# Replace environment variables in env.js
envsubst < /usr/share/nginx/html/env.js > /usr/share/nginx/html/env.js.tmp
mv /usr/share/nginx/html/env.js.tmp /usr/share/nginx/html/env.js

# Execute the main container command
exec "$@" 