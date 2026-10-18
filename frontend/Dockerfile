# ── AGRIFLOW-AI React frontend (Vite dev server for local Compose/Podman) ─────
FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 3000

# --host 0.0.0.0 so the port publish works from the container
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
