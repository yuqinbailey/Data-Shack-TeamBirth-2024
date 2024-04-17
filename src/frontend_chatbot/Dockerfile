# Use the official Nginx image as a parent image
FROM nginx:alpine

# Remove the default nginx index page
RUN rm -rf /usr/share/nginx/html/*

# Copy the static assets
COPY ./static /usr/share/nginx/html/static

# Copy the templates
COPY ./templates /usr/share/nginx/html

# Copy the custom Nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port 80
EXPOSE 80

# Start Nginx when the container has provisioned.
CMD ["nginx", "-g", "daemon off;"]
