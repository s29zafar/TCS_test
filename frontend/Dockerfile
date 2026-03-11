# Use Node.js for building
FROM node:20-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY package.json .
RUN npm install

# Copy project files
COPY . .

# Expose port
EXPOSE 5173

# Start command
CMD ["npm", "run", "dev", "--", "--host"]
