FROM node:20-slim

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (handle catalog: syntax)
RUN npm install

# Copy source code
COPY . .

# Build if needed (your tsconfig has noEmit, so skip compile)
# RUN npm run build

# Start the bot
CMD ["npm", "start"]
