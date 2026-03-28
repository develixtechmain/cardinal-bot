FROM node:22.20.0-alpine3.22 AS build
WORKDIR /app

COPY package*.json ./
RUN npm ci


COPY . .
COPY production.env .env

RUN npm run build

FROM node:22.20.0-alpine3.22
WORKDIR /app

COPY package*.json ./
RUN npm ci --omit=dev

COPY --from=build /app/dist ./dist

EXPOSE 3000
LABEL loki.include=true loki.service.name=app

CMD ["npx", "serve", "-s", "dist", "-l", "3000"]
