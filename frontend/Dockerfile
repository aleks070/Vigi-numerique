FROM node:20-alpine

WORKDIR /app

# Dépendances
COPY package*.json ./
RUN npm install

# Code source
COPY . .

# Exposition du port Vite
EXPOSE 3000

# Démarrage avec host 0.0.0.0 pour être accessible depuis Docker
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
