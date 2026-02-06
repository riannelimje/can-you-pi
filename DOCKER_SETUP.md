# 🐳 Docker Setup Guide

## Quick Start

### Option 1: Using Docker Compose (Recommended)

```bash
# 1. Make sure you have .env file with GROQ_API_KEY
# If you don't have .env yet, create it:
# echo "GROQ_API_KEY=your_key_here" > .env
# Otherwise skip to step 2

# 2. Build and run
docker compose up -d

# 3. View logs
docker compose logs -f

# 4. Stop
docker compose down
```

### Option 2: Using Docker Commands

```bash
# 1. Build the image
docker build -t can-you-pi:latest .

# 2. Run the container
docker run -d \
  --name can-you-pi \
  -p 8000:8000 \
  -e GROQ_API_KEY=your_key_here \
  can-you-pi:latest

# 3. View logs
docker logs -f can-you-pi

# 4. Stop and remove
docker stop can-you-pi
docker rm can-you-pi
```

## Access the Application

Once running, access:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Environment Variables

Required:
- `GROQ_API_KEY` - Your Groq API key from https://console.groq.com/

## Development Mode

For development with auto-reload, use docker-compose with volumes:

```bash
# The docker-compose.yml already has volumes configured
docker-compose up
```

Any code changes will trigger uvicorn's auto-reload.

## Production Deployment

### 1. Build for Production

```bash
# Remove development volumes from docker-compose.yml
# Then build
docker-compose build --no-cache
```

### 2. Multi-stage Build (Advanced)

For smaller images, consider this optimized Dockerfile:

```dockerfile
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. Deploy to Cloud

#### Deploy to Railway
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

#### Deploy to Render
1. Connect your GitHub repo to Render
2. Create a new Web Service
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variable: `GROQ_API_KEY`

#### Deploy to Google Cloud Run
```bash
# Build and push
gcloud builds submit --tag gcr.io/YOUR_PROJECT/can-you-pi

# Deploy
gcloud run deploy can-you-pi \
  --image gcr.io/YOUR_PROJECT/can-you-pi \
  --platform managed \
  --region us-central1 \
  --set-env-vars GROQ_API_KEY=your_key
```

## Docker Commands Cheat Sheet

```bash
# Build
docker build -t can-you-pi:latest .

# Run
docker run -d -p 8000:8000 --env-file .env can-you-pi

# View logs
docker logs -f can-you-pi

# Execute commands inside container
docker exec -it can-you-pi bash

# Stop
docker stop can-you-pi

# Remove
docker rm can-you-pi

# Remove image
docker rmi can-you-pi

# View running containers
docker ps

# View all containers
docker ps -a

# Clean up everything
docker system prune -a
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker logs can-you-pi

# Common issues:
# 1. Missing GROQ_API_KEY
# 2. Port 8000 already in use
# 3. Permission issues with volumes
```

### Port already in use
```bash
# Find what's using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
docker run -p 8080:8000 can-you-pi
```

### Permission denied errors
```bash
# Make sure files are readable
chmod -R 755 .

# Check .dockerignore doesn't exclude needed files
```

## Performance Tips

1. **Use .dockerignore** - Already configured to exclude unnecessary files
2. **Multi-stage builds** - Reduces final image size
3. **Layer caching** - requirements.txt is copied first for better caching
4. **Non-root user** - Runs as appuser for security
5. **Health checks** - Ensures container is healthy

## Security Best Practices

✅ **Implemented:**
- Non-root user (appuser)
- Minimal base image (python:3.11-slim)
- No sensitive data in image
- Health checks enabled

⚠️ **Additional recommendations:**
- Use secrets management (AWS Secrets Manager, HashiCorp Vault)
- Scan images for vulnerabilities: `docker scan can-you-pi`
- Use specific version tags instead of `latest`
- Implement rate limiting in production
- Add SSL/TLS with reverse proxy (nginx)

## Monitoring

### View resource usage
```bash
docker stats can-you-pi
```

### View health status
```bash
docker inspect --format='{{.State.Health.Status}}' can-you-pi
```

### Export logs
```bash
docker logs can-you-pi > app.log 2>&1
```

## Need Help?

- Check logs: `docker logs -f can-you-pi`
- Inspect container: `docker inspect can-you-pi`
- Access shell: `docker exec -it can-you-pi bash`
- Test API: `curl http://localhost:8000/`
