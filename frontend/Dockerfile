# Frontend Dockerfile for Render static deployment
FROM node:18-alpine AS build

# Set working directory
WORKDIR /app

# Copy package files
COPY frontend/scriptCut/package*.json ./

# Install dependencies
RUN npm install

# Install lucide-react dependency
RUN npm install lucide-react

# Copy source code
COPY frontend/scriptCut/ ./

# Build the application
ENV VITE_API_BASE_URL=https://scriptssor.onrender.com
RUN npm run build

# Use nginx to serve the static files
FROM nginx:alpine

# Copy built files
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port
EXPOSE 10000

# Start nginx
CMD ["nginx", "-g", "daemon off;"]