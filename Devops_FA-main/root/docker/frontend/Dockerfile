FROM nginx:1.27-alpine

COPY nginx.conf \
    /etc/nginx/conf.d/default.conf

COPY index.html \
    /usr/share/nginx/html/index.html

COPY style.css \
    /usr/share/nginx/html/style.css

COPY script.js \
    /usr/share/nginx/html/script.js

EXPOSE 80

HEALTHCHECK --interval=30s \
    --timeout=5s \
    --start-period=5s \
    --retries=3 \
    CMD wget -q --spider http://localhost/ || exit 1
