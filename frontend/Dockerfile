# syntax=docker/dockerfile:1.7
ARG NODE_VERSION=20

# ── builder ──────────────────────────────────────────────────────
FROM node:${NODE_VERSION}-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --legacy-peer-deps || npm install --legacy-peer-deps
COPY . .
RUN npm run build

# ── dev ──────────────────────────────────────────────────────────
FROM node:${NODE_VERSION}-alpine AS dev
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --legacy-peer-deps || npm install --legacy-peer-deps
EXPOSE 5173
CMD ["npm", "run", "dev"]

# ── runtime ──────────────────────────────────────────────────────
FROM nginx:1.27-alpine AS runtime
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
HEALTHCHECK CMD wget -qO- http://localhost/ || exit 1
