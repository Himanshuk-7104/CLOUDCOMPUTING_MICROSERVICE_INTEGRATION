# auth-backend/Dockerfile

# Use an official Node.js runtime as a parent image (choose a version suitable for your code)
FROM node:18-alpine

# Set the working directory in the container
WORKDIR /app

# Copy package.json and package-lock.json (or yarn.lock)
# This step leverages Docker cache for dependencies
COPY package*.json ./

# Install only production dependencies
RUN npm ci --only=production

# Copy the rest of the application code into the container
COPY . .

# Make your backend's port available to the network (the port your server.js listens on)
EXPOSE 3001

# Define the command to run your app using node
CMD [ "node", "server.js" ]