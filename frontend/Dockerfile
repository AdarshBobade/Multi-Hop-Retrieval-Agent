FROM node:22-alpine AS builder

WORKDIR /app

# Copy package files first for Docker layer caching
COPY package.json package-lock.json ./

# Install exact dependencies from package-lock.-json
RUN npm ci

# Copy the rest of the frontend source
COPY . .


RUN npm run build


FROM nginx:alpine
RUN rm -rf /usr/share/nginx/html/*
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
EXPOSE 10000
CMD ["nginx", "-g", "daemon off;"]