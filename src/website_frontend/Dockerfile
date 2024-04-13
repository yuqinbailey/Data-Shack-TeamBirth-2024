FROM nginx:alpine

# Remove default NGINX static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy the configuration file
COPY ./config/nginx.config /etc/nginx/nginx.conf

# Copy the static files
COPY ./static /usr/share/nginx/html/static

# Copy the templates
COPY ./templates /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
