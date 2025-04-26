# Use a specific Python version if possible, slim is good
FROM python:3.9-slim

WORKDIR /app


RUN apt-get update && apt-get install -y --no-install-recommends wget gnupg curl ca-certificates && \
    # Add MongoDB GPG key
    curl -fsSL https://pgp.mongodb.com/server-7.0.asc | \
       gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg && \
    # Add MongoDB repository using the key
    echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] http://repo.mongodb.org/apt/debian buster/mongodb-org/7.0 main" | \
       tee /etc/apt/sources.list.d/mongodb-org-7.0.list && \
    # Update apt and install mongosh (optional, but kept as per original)
    apt-get update && \
    apt-get install -y --no-install-recommends mongodb-mongosh && \
    # Clean up APT caches and lists
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application using Uvicorn
# Use --host 0.0.0.0 to be accessible externally
# --reload is useful for development but should generally be removed for production images
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]