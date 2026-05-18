# Docker Hub Deployment Workflow

This document explains how the Docker Hub integration works and how to manage deployments.

## Workflow Overview

```
┌─────────────────┐
│  Developer      │
│  Pushes Code    │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│  GitHub Actions     │
│  - Build Image      │
│  - Run Tests        │
│  - Tag Image        │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   Docker Hub        │
│  Store Images       │
│  username/smartnyumba│
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Hetzner VPS        │
│  - Pull Image       │
│  - Run Container    │
└─────────────────────┘
```

## Image Tagging Strategy

The GitHub Actions workflow creates multiple tags for each build:

1. **`latest`** - Always points to the most recent main branch build
2. **`main-<git-sha>`** - Specific commit from main branch (e.g., `main-abc1234`)
3. **`main`** - Always points to the most recent main branch build

### Examples:
```
yourusername/smartnyumba:latest
yourusername/smartnyumba:main
yourusername/smartnyumba:main-a1b2c3d
```

## Deployment Process

### Automatic Deployment (Main Branch)

When you push to the `main` branch:

1. **GitHub Actions triggers** the workflow
2. **Build phase:**
   - Checks out code
   - Sets up Docker Buildx
   - Logs into Docker Hub
   - Builds the image
   - Tags with multiple tags
   - Pushes to Docker Hub
3. **Deploy phase:**
   - Connects to VPS via SSH
   - Copies deployment files
   - Creates `.env` file
   - Pulls latest image from Docker Hub
   - Restarts containers

### Manual Deployment

If you need to deploy a specific version:

```bash
# SSH to VPS
ssh root@178.105.35.41

# Navigate to project
cd /opt/smartnyumba

# Set the image tag you want
export IMAGE_TAG=main-abc1234  # or 'latest'

# Deploy
./deploy.sh
```

## Rollback to Previous Version

If something goes wrong, you can easily rollback:

### Method 1: Rollback via Environment Variable

```bash
# SSH to VPS
ssh root@178.105.35.41
cd /opt/smartnyumba

# Edit .env file
nano .env

# Change IMAGE_TAG to previous version
IMAGE_TAG=main-abc1234  # Replace with actual commit hash

# Save and exit, then deploy
./deploy.sh
```

### Method 2: Quick Rollback via Command

```bash
ssh root@178.105.35.41 "cd /opt/smartnyumba && export IMAGE_TAG=main-abc1234 && ./deploy.sh"
```

### Method 3: Find Previous Working Version

```bash
# List recent images on Docker Hub
curl -s "https://hub.docker.com/v2/repositories/YOUR_USERNAME/smartnyumba/tags/" | jq -r '.results[].name'

# Or check in GitHub Actions tab to see which commits were deployed
```

## Viewing Available Images

### On Docker Hub:
Visit: https://hub.docker.com/r/YOUR_USERNAME/smartnyumba/tags

### Via CLI:
```bash
# Install jq if not already installed: apt install jq

# List all tags
curl -s "https://hub.docker.com/v2/repositories/YOUR_USERNAME/smartnyumba/tags/" | jq -r '.results[] | "\(.name) - Updated: \(.last_updated)"'
```

## Managing Images

### Pull Specific Version on VPS
```bash
docker pull yourusername/smartnyumba:main-abc1234
```

### Check Current Running Image
```bash
docker ps --format "{{.Image}}"
```

### Remove Old Local Images
```bash
# On VPS
docker image prune -a -f
```

## Docker Hub Storage Limits

Free Docker Hub accounts have limits:
- **Storage**: Unlimited repositories
- **Bandwidth**: Limited pull rate (100 pulls per 6 hours for anonymous users)
- **Image retention**: No automatic deletion

### Best Practices:
1. Delete old images you no longer need
2. Keep only recent versions (e.g., last 10 builds)
3. Consider Docker Hub Pro if you hit rate limits

### Cleanup Old Images (Manual)

Go to Docker Hub → Your Repository → Tags → Delete old tags

## Troubleshooting

### Issue: "unauthorized: incorrect username or password"

**Solution:**
- Verify `DOCKERHUB_USERNAME` in GitHub Secrets
- Regenerate `DOCKERHUB_TOKEN` in Docker Hub
- Update the token in GitHub Secrets

### Issue: "manifest unknown"

**Solution:**
- The image tag doesn't exist on Docker Hub
- Check available tags: `docker search yourusername/smartnyumba`
- Use `latest` tag or verify the commit hash

### Issue: "too many requests"

**Solution:**
- Docker Hub rate limit hit
- Wait 6 hours or upgrade to Docker Hub Pro
- Use authentication (already configured in workflow)

### Issue: Build fails in GitHub Actions

**Solution:**
1. Check GitHub Actions logs
2. Verify Dockerfile syntax
3. Check if dependencies are available
4. Verify Docker Hub credentials

### Issue: Image pulls slowly on VPS

**Solution:**
- Normal for first pull (downloading all layers)
- Subsequent pulls use cached layers (faster)
- Consider using a CDN or mirror if needed

## CI/CD Pipeline Details

The `.github/workflows/deploy.yml` workflow:

```yaml
jobs:
  build-and-push:
    - Checkout code
    - Setup Docker Buildx (multi-platform builds)
    - Login to Docker Hub (using secrets)
    - Extract metadata (tags, labels)
    - Build and push (with layer caching)

  deploy:
    needs: build-and-push  # Waits for build to complete
    - Setup SSH
    - Copy files to VPS
    - Create .env file
    - Run deploy.sh (pulls from Docker Hub)
```

## Environment Variables

### Required on VPS (.env file):
```bash
DOCKERHUB_USERNAME=your-username  # Your Docker Hub username
IMAGE_TAG=latest                   # Which tag to deploy (default: latest)
```

### Required in GitHub Secrets:
```bash
DOCKERHUB_USERNAME  # Docker Hub username
DOCKERHUB_TOKEN     # Docker Hub access token (not password!)
SSH_PRIVATE_KEY     # SSH key for VPS access
# ... other secrets
```

## Benefits of This Approach

✅ **Faster Deployments**: No building on VPS
✅ **Consistent Images**: Same image across all environments
✅ **Easy Rollbacks**: Just change the tag
✅ **Version History**: All builds stored on Docker Hub
✅ **Bandwidth Savings**: Pull only changed layers
✅ **Multi-environment**: Can deploy same image to staging/production
✅ **Disaster Recovery**: Images backed up on Docker Hub

## Security Considerations

1. **Never commit Docker Hub credentials** to git
2. **Use access tokens**, not passwords
3. **Limit token permissions** to what's needed
4. **Rotate tokens periodically**
5. **Use private repositories** if code is sensitive (requires Docker Hub Pro)

## Advanced: Using Different Environments

You can deploy different versions to different environments:

```bash
# Production (on port 8080)
export IMAGE_TAG=latest
docker-compose -f docker-compose.yml up -d

# Staging (on port 8081)
export IMAGE_TAG=main-dev123
docker-compose -f docker-compose.staging.yml up -d
```

## Monitoring

### Check Deployment Status
```bash
# View GitHub Actions
# Go to: https://github.com/YOUR_USERNAME/YOUR_REPO/actions

# Or via CLI (requires gh CLI)
gh run list
gh run view <run-id>
```

### Check Running Containers
```bash
ssh root@178.105.35.41 "docker ps"
```

### View Logs
```bash
ssh root@178.105.35.41 "cd /opt/smartnyumba && docker-compose logs -f"
```

## Summary

This Docker Hub workflow provides:
- Automated builds on every push
- Centralized image storage
- Fast deployments
- Easy rollbacks
- Version control for containers

All while keeping your VPS lightweight and deployments fast!
