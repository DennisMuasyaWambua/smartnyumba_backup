# SmartNyumba Deployment Guide

This guide explains how to deploy the SmartNyumba application to your Hetzner VPS using Docker and GitHub Actions for automated deployments.

## Architecture Overview

- **VPS**: Hetzner (178.105.35.41)
- **Containerization**: Docker & Docker Compose
- **Web Server**: Nginx (reverse proxy)
- **Application Server**: Gunicorn
- **Database**: Railway PostgreSQL (external)
- **CI/CD**: GitHub Actions
- **Port**: 8080 (to avoid conflicts with existing services)

## Prerequisites

1. Docker Hub account (free at https://hub.docker.com)
2. Hetzner VPS with root access
3. GitHub repository for your code
4. Railway PostgreSQL database (already configured)

## Setup Instructions

### Step 0: Setup Docker Hub

1. Create a Docker Hub account at https://hub.docker.com (if you don't have one)

2. Create an access token for GitHub Actions:
   - Login to Docker Hub
   - Go to Account Settings → Security
   - Click "New Access Token"
   - Name: "GitHub Actions SmartNyumba"
   - Permissions: Read, Write, Delete
   - Click "Generate"
   - **Copy the token immediately** (you won't see it again!)

3. Note your Docker Hub username (you'll need it for GitHub Secrets)

### Step 1: Setup SSH Access

1. Generate an SSH key pair on your local machine (if you don't have one):
   ```bash
   ssh-keygen -t ed25519 -C "github-actions-smartnyumba"
   ```

2. Copy the public key to your VPS:
   ```bash
   ssh-copy-id root@178.105.35.41
   ```

3. Test SSH connection:
   ```bash
   ssh root@178.105.35.41
   ```

### Step 2: Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and Variables → Actions → New repository secret

Add the following secrets:

#### Required Secrets:

**Docker Hub:**
- `DOCKERHUB_USERNAME`: Your Docker Hub username
- `DOCKERHUB_TOKEN`: The access token you created in Step 0

**SSH Access:**
- `SSH_PRIVATE_KEY`: Your private SSH key (content of `~/.ssh/id_ed25519`)

**Django:**
- `SECRET_KEY`: Django secret key (generate with `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`)

#### Email Settings:
- `EMAIL_HOST`: smtp.gmail.com (or your SMTP server)
- `EMAIL_HOST_USER`: your-email@gmail.com
- `EMAIL_HOST_PASSWORD`: your-app-password
- `DEFAULT_FROM_EMAIL`: noreply@smartnyumba.com
- `SERVER_EMAIL`: server@smartnyumba.com
- `EMAIL_USE_TLS`: True
- `EMAIL_USE_SSL`: False
- `EMAIL_PORT`: 587

#### Safaricom/M-Pesa Settings:
- `SAFARICOM_AUTH_ENDPOINT`
- `SAFARICOM_AUTH_KEY`
- `SAFARICOM_AUTH_CONSUMER_SECRET`
- `SAFARICOM_STK_PUSH`
- `SAFARICOM_PASS_KEY`
- `BUSINESS_SHORT_CODE`
- `TILLNUMBER`

#### B2C Settings:
- `SAFARICOM_BC2_AUTH_KEY`
- `SAFARICOM_B2C_CONSUMER_TIME`
- `SAFARICOM_B2C_ENDPOINT`
- `SAFARICOM_B2C_INITIATOR_PASSWORD`
- `SAFARICOM_B2C_INITIATOR_NAME`
- `SAFARICOM_B2C_QUEUETIMEOUTURL`
- `SAFARICOM_B2C_RESULTURL`
- `SAFARICOM_B2C_PARTYA`
- `B2C_CER`

#### Stripe Settings:
- `STRIPE_SECRET_KEY`
- `SUCCESS_URL`
- `CANCEL_URL`

### Step 3: Initial VPS Setup (One-time)

SSH into your VPS and run:

```bash
# Update system
apt update && apt upgrade -y

# Install Docker (if not already installed)
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl start docker
systemctl enable docker

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create deployment directory
mkdir -p /opt/smartnyumba

# Verify installations
docker --version
docker-compose --version
```

### Step 4: Deploy

#### Option A: Automatic Deployment (GitHub Actions) - Recommended

1. Push your code to the `main` branch:
   ```bash
   git add .
   git commit -m "Setup deployment"
   git push origin main
   ```

2. GitHub Actions will automatically:
   - **Build the Docker image** on GitHub servers
   - **Push the image to Docker Hub**
   - Copy deployment files to the VPS
   - Create the `.env` file with secrets
   - **Pull the image from Docker Hub** on VPS
   - Run migrations
   - Start the containers

3. Monitor deployment in GitHub Actions tab

**Why Docker Hub?**
- ✅ Faster deployments (no building on VPS)
- ✅ Consistent images across environments
- ✅ Easy rollback to specific versions
- ✅ VPS doesn't need build tools installed
- ✅ Can reuse images for multiple deployments

#### Option B: Manual Deployment

1. SSH into your VPS:
   ```bash
   ssh root@178.105.35.41
   ```

2. Clone your repository:
   ```bash
   cd /opt/smartnyumba
   git clone <your-repo-url> .
   ```

3. Create `.env` file (use `.env.example` as template):
   ```bash
   cp .env.example .env
   nano .env  # Edit with your actual values
   ```

4. Run deployment script:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

## Accessing the Application

- **HTTP**: http://178.105.35.41:8080
- **API**: http://178.105.35.41:8080/apps/api/v1/

## Common Commands

### View logs:
```bash
cd /opt/smartnyumba
docker-compose logs -f
```

### Restart services:
```bash
cd /opt/smartnyumba
docker-compose restart
```

### Stop services:
```bash
cd /opt/smartnyumba
docker-compose down
```

### Start services:
```bash
cd /opt/smartnyumba
docker-compose up -d
```

### Run migrations:
```bash
cd /opt/smartnyumba
docker-compose exec web python manage.py migrate
```

### Create superuser:
```bash
cd /opt/smartnyumba
docker-compose exec web python manage.py createsuperuser
```

### Access Django shell:
```bash
cd /opt/smartnyumba
docker-compose exec web python manage.py shell
```

### Check container status:
```bash
cd /opt/smartnyumba
docker-compose ps
```

## Setting up Domain (Optional)

If you want to use a domain name instead of IP:

1. Point your domain's A record to: 178.105.35.41
2. Update `ALLOWED_HOSTS` in `.env` file
3. Update GitHub Actions workflow with your domain
4. Optionally set up SSL with Let's Encrypt

### Setting up SSL (HTTPS):

```bash
# Install certbot
apt install certbot python3-certbot-nginx -y

# Get SSL certificate
certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal is set up automatically
```

## Troubleshooting

### Check if containers are running:
```bash
docker ps
```

### Check container logs:
```bash
docker-compose logs web
docker-compose logs nginx
```

### Restart a specific service:
```bash
docker-compose restart web
docker-compose restart nginx
```

### Rebuild containers:
```bash
cd /opt/smartnyumba
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Check disk space:
```bash
df -h
docker system df
```

### Clean up unused Docker resources:
```bash
docker system prune -a
```

## Email Configuration Note

Since Railway blocks SMTP, deploying to VPS allows you to:
- Use Gmail SMTP (with app password)
- Use SendGrid, Mailgun, or other email services
- Run your own mail server

Make sure to configure the email settings in GitHub Secrets correctly.

## Isolation from Other Projects

This deployment is completely isolated because:
- Uses separate Docker containers
- Runs on port 8080 (different from standard 80/443)
- Has its own Docker network (`smartnyumba_network`)
- All data is contained in Docker volumes

## Database Note

The application uses Railway's PostgreSQL database:
- Connection string is already configured in the workflow
- No local database container needed
- Migrations run automatically on deployment

## Monitoring

### Check application health:
```bash
curl http://178.105.35.41:8080/health
```

### Monitor resource usage:
```bash
docker stats
```

## Security Recommendations

1. **Firewall**: Configure UFW to only allow necessary ports:
   ```bash
   ufw allow 22/tcp
   ufw allow 8080/tcp
   ufw enable
   ```

2. **SSH**: Disable password authentication, use keys only
3. **Updates**: Keep system and Docker updated regularly
4. **Secrets**: Never commit `.env` file to git
5. **Backups**: Regular database backups from Railway dashboard

## Support

For issues or questions, check:
- Container logs: `docker-compose logs`
- GitHub Actions logs in your repository
- Railway database logs in Railway dashboard
