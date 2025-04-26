# auth-frontend/Dockerfile

# --- Stage 1: Build the React App ---
    FROM node:18-alpine AS build

    WORKDIR /app
    
    # Copy package manifests
    COPY package*.json ./
    
    # Install dependencies
    RUN npm install
    
    # Copy the rest of the source code
    COPY . .
    
    # Build the production application (Vite typically builds to /dist)
    # Replace 'build' with your actual build script if different
    RUN npm run build
    
    # --- Stage 2: Serve with Nginx ---
    FROM nginx:stable-alpine
    
    # Copy the static build output from the 'build' stage to Nginx html directory
    COPY --from=build /app/dist /usr/share/nginx/html
    
    # Copy our custom Nginx configuration
    COPY nginx.conf /etc/nginx/conf.d/default.conf
    
    # Expose port 80 (Nginx default)
    EXPOSE 80
    
    # Default command to start Nginx when the container launches
    CMD ["nginx", "-g", "daemon off;"]