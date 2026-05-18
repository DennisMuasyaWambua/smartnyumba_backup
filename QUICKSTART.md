# SmartNyumba Quick Start Guide

Get your SmartNyumba application deployed to Hetzner VPS in minutes!

## 🚀 Quick Setup (4 Steps)

### Step 0: Setup Docker Hub (One-time, 2 minutes)

1. Create a Docker Hub account at https://hub.docker.com (if you don't have one)
2. Create an access token:
   - Go to Account Settings → Security → New Access Token
   - Name it "GitHub Actions"
   - Copy the token (you won't see it again!)

### Step 1: Setup VPS (One-time, 5 minutes)

1. Copy the setup script to your VPS:
   ```bash
   scp vps-setup.sh root@178.105.35.41:/root/
   ```

2. SSH into VPS and run setup:
   ```bash
   ssh root@178.105.35.41
   bash vps-setup.sh
   ```

This installs Docker, Docker Compose, configures firewall, and prepares the environment.

### Step 2: Configure GitHub Secrets (One-time, 5 minutes)

Go to: GitHub Repository → Settings → Secrets and Variables → Actions

#### Minimum Required Secrets:
```
# Docker Hub (REQUIRED)
DOCKERHUB_USERNAME=<your-dockerhub-username>
DOCKERHUB_TOKEN=<your-dockerhub-access-token>

# SSH Access (REQUIRED)
SSH_PRIVATE_KEY=<your-private-ssh-key>

# Django (REQUIRED)
SECRET_KEY=<django-secret-key>

# Email (REQUIRED)
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=<your-email@gmail.com>
EMAIL_HOST_PASSWORD=<your-app-password>
DEFAULT_FROM_EMAIL=noreply@smartnyumba.com
SERVER_EMAIL=server@smartnyumba.com
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_PORT=587
```

Copy all other secrets from your Railway environment or .env file.

### Step 3: Deploy (Automatic, 2 minutes)

```bash
git add .
git commit -m "Setup Docker deployment"
git push origin main
```

GitHub Actions will automatically deploy to your VPS!

## ✅ Verify Deployment

Check your application:
```bash
curl http://178.105.35.41:8080/health
```

Or visit in browser: http://178.105.35.41:8080

## 📋 Files Created

- `Dockerfile` - Container image definition
- `docker-compose.yml` - Multi-container orchestration
- `.dockerignore` - Files to exclude from image
- `nginx.conf` - Web server configuration
- `.github/workflows/deploy.yml` - CI/CD pipeline
- `deploy.sh` - Deployment automation script
- `vps-setup.sh` - VPS initial setup script
- `.env.example` - Environment variables template

## 🔧 Common Operations

### View Logs:
```bash
ssh root@178.105.35.41
cd /opt/smartnyumba
docker-compose logs -f
```

### Restart Application:
```bash
ssh root@178.105.35.41
cd /opt/smartnyumba
docker-compose restart
```

### Manual Deployment:
```bash
ssh root@178.105.35.41
cd /opt/smartnyumba
git pull origin main
./deploy.sh
```

## 🎯 Key Features

✅ **Docker Hub Integration**: Images built in GitHub, pulled on VPS (faster deployments)
✅ **Fully Isolated**: Runs on port 8080, won't interfere with other projects
✅ **Auto-Deploy**: Push to main branch = automatic deployment
✅ **Email Working**: VPS allows SMTP (Railway blocks it)
✅ **External Database**: Uses Railway PostgreSQL (no local DB needed)
✅ **Health Checks**: Automatic container health monitoring
✅ **Zero Downtime**: Containers auto-restart on failure
✅ **Easy Rollback**: Use specific image tags to rollback versions

## 🆘 Troubleshooting

### Deployment Failed?
Check GitHub Actions logs in your repository's Actions tab.

### Application Not Responding?
```bash
ssh root@178.105.35.41
cd /opt/smartnyumba
docker-compose ps  # Check if containers are running
docker-compose logs web  # Check application logs
```

### Database Connection Issues?
Verify Railway database URL is correct in GitHub Secrets.

### Email Not Sending?
Check email configuration in GitHub Secrets (especially app password).

## 📚 Full Documentation

See `DEPLOYMENT.md` for complete documentation including:
- SSL/HTTPS setup
- Domain configuration
- Security hardening
- Monitoring setup
- Backup strategies

## 🔐 Security Notes

- Never commit `.env` file
- Use strong passwords for all services
- Keep SSH key secure
- Enable firewall on VPS
- Regular system updates: `apt update && apt upgrade`

## 🎉 You're Done!

Your SmartNyumba application is now:
- Running on: http://178.105.35.41:8080
- Auto-deploying on git push
- Isolated from other VPS projects
- Using external Railway database
- Sending emails via SMTP (not blocked!)

Need help? Check logs or refer to `DEPLOYMENT.md` for detailed instructions.
