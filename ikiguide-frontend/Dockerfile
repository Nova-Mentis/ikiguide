# Use Node.js as the base image
FROM node:18

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json (or yarn.lock)
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Build the application
RUN npm run build

# Install serve to serve the build files
RUN npm install -g serve

# Expose the port the app runs on
EXPOSE 443
EXPOSE 3000

# Command to serve the build with HTTPS
CMD sh -c "serve -s build -l 443 --ssl-cert /etc/letsencrypt/live/ikiguide.nova-mentis.com/cert.pem --ssl-key /etc/letsencrypt/live/ikiguide.nova-mentis.com/privkey.pem & serve -s build -l 3000"

# Set labels for Docker Hub 
LABEL org.opencontainers.image.source="https://github.com/Nova-Mentis/ikiguide"
LABEL org.opencontainers.image.title="ikiguide-frontend"