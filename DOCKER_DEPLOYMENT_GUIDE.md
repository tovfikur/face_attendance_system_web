# Docker Deployment Guide - Face Attendance System

**Date**: November 5, 2024
**Status**: ✅ Complete Docker Setup Ready
**Version**: 1.0.0

---

## 🐳 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (5 minutes)](#quick-start-5-minutes)
3. [Architecture Overview](#architecture-overview)
4. [Detailed Setup](#detailed-setup)
5. [Configuration](#configuration)
6. [Deployment](#deployment)
7. [Verification](#verification)
8. [Troubleshooting](#troubleshooting)
9. [Monitoring](#monitoring)
10. [Scaling](#scaling)

---

## Prerequisites

### Required Software

```bash
# Check these are installed and updated:
docker --version          # Docker 20.10+
docker-compose --version  # Docker Compose 2.0+

# Installation:
# - Docker: https://docs.docker.com/get-docker/
# - Docker Compose: https://docs.docker.com/compose/install/
```

### System Requirements

```
CPU:        2+ cores (4+ recommended)
RAM:        4GB minimum (8GB+ recommended)
Disk:       20GB minimum (50GB+ for production)
Network:    Stable internet connection
OS:         Linux, macOS, or Windows (WSL2)
```

### Ports Required

```
80      - HTTP (Frontend + API)
443     - HTTPS (when configured)
5432    - PostgreSQL
6379    - Redis
9000    - MinIO Object Storage
9001    - MinIO Console
8000    - Backend API (internal only)
```

---

## Quick Start (5 minutes)

### 1. Clone/Navigate to Project
```bash
cd face_attendance_system_web
```

### 2. Copy Environment File
```bash
cp .env.docker .env
# Edit .env if needed (default values work for development)
```

### 3. Start All Services
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Wait for Services to Start
```bash
# Check status
docker-compose -f docker-compose.prod.yml ps

# Wait until all services show "Up" status (about 30 seconds)
```

### 5. Access the System
```
Frontend:       http://localhost
API:            http://localhost/api/v1
MinIO Console:  http://localhost:9001
              (user: minioadmin, pass: minioadmin123)
```

### 6. Default Login Credentials
```
Username: testuser
Password: testpass123

(Create new users via API or backend admin)
```

---

## Architecture Overview

### Services

```
┌─────────────────────────────────────────────────────────┐
│                     Nginx (Reverse Proxy)               │
│            Port 80 (HTTP) / 443 (HTTPS)                 │
└──────────────┬──────────────────────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
  ┌────▼─────┐    ┌────▼──────┐
  │ Frontend  │    │  Backend   │
  │ React     │    │  FastAPI   │
  │ Port 80   │    │ Port 8000  │
  └────┬──────┘    └────┬───────┘
       │                │
       └────────┬───────┘
              ┌─┴─┬───────┬──────┐
              │   │       │      │
         ┌────▼─┐ │   ┌───▼──┐ ┌▼──────┐
         │Celery│ │   │Redis │ │MinIO  │
         │Tasks │ │   │Cache │ │Storage│
         └──────┘ │   └──────┘ └───────┘
                  │
              ┌───▼────┐
              │Postgres│
              │Database│
              └────────┘
```

### Services Breakdown

| Service | Purpose | Port | Technology |
|---------|---------|------|-----------|
| Nginx | Reverse Proxy | 80/443 | Nginx 1.27 |
| Frontend | React App | (internal) | React 19 + Node |
| Backend | REST API | 8000 | FastAPI |
| PostgreSQL | Database | 5432 | PostgreSQL 16 |
| Redis | Cache & Queue | 6379 | Redis 7 |
| MinIO | Object Storage | 9000/9001 | MinIO |
| Celery Worker | Background Tasks | (internal) | Celery |
| Celery Beat | Task Scheduler | (internal) | Celery Beat |

---

## Detailed Setup

### Step 1: Prepare Environment

```bash
# Navigate to project root
cd face_attendance_system_web

# Copy environment file
cp .env.docker .env

# (Optional) Edit for custom configuration
nano .env  # or use your editor
```

### Step 2: Build Images (if needed)

```bash
# Build specific images
docker-compose -f docker-compose.prod.yml build backend
docker-compose -f docker-compose.prod.yml build frontend

# Or rebuild all
docker-compose -f docker-compose.prod.yml build --no-cache
```

### Step 3: Create Directories

```bash
# Create necessary directories
mkdir -p docker/ssl
mkdir -p data/postgres
mkdir -p data/redis
mkdir -p data/minio
mkdir -p logs

# Set permissions
chmod 755 docker/
chmod 755 data/
chmod 755 logs/
```

### Step 4: Start Services

```bash
# Start in background
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Watch specific service
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f postgres
```

### Step 5: Initialize Database

```bash
# Run migrations (if applicable)
docker-compose -f docker-compose.prod.yml exec backend \
  alembic upgrade head

# Create admin user (if needed)
docker-compose -f docker-compose.prod.yml exec backend \
  python -m app.scripts.create_admin \
  --username admin \
  --password your_secure_password
```

### Step 6: Verify Health

```bash
# Check all services
docker-compose -f docker-compose.prod.yml ps

# Test backend health
curl http://localhost/api/v1/health

# Test frontend
curl http://localhost/
```

---

## Configuration

### Environment Variables

Located in `.env` (copy from `.env.docker`):

**Critical Variables**:
```env
# Database
DB_USER=postgres
DB_PASSWORD=change_in_production
DB_NAME=face_attendance

# Redis
REDIS_URL=redis://redis:6379/0

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=change_in_production

# Security (IMPORTANT - Change these!)
SECRET_KEY=change-this-to-secure-random-string-in-production
ALLOWED_ORIGINS=http://localhost,http://your-domain.com
```

**For Production**:
```env
# 1. Change all passwords
DB_PASSWORD=SecurePassword123!
MINIO_ROOT_PASSWORD=SecurePassword123!
SECRET_KEY=GenerateSecureKeyHere12345678901234567890

# 2. Configure CORS
ALLOWED_ORIGINS=https://your-domain.com

# 3. Enable HTTPS
SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
SSL_KEY_PATH=/etc/nginx/ssl/key.pem

# 4. Disable debug
DEBUG=false
VITE_DEBUG=false
```

### Docker Compose Override (Local Development)

Create `docker-compose.override.yml`:

```yaml
version: '3.9'

services:
  backend:
    environment:
      - DEBUG=true
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    environment:
      - VITE_DEBUG=true
```

---

## Deployment

### Local/Development Deployment

```bash
# Start everything
docker-compose -f docker-compose.prod.yml up -d

# Monitor
docker-compose -f docker-compose.prod.yml logs -f

# Stop when done
docker-compose -f docker-compose.prod.yml down
```

### Production Deployment

#### Step 1: Secure Your Setup

```bash
# Generate secure secret key
openssl rand -base64 32

# Update .env with:
# - Strong passwords
# - Your domain
# - SSL certificates
# - Secure Redis password
# - Secure database password
```

#### Step 2: Prepare SSL/TLS

```bash
# Copy your SSL certificates
cp /path/to/cert.pem docker/ssl/
cp /path/to/key.pem docker/ssl/

# Update nginx.conf to enable HTTPS
# Uncomment the HTTPS section and add your domain
```

#### Step 3: Deploy

```bash
# Ensure .env is properly configured
cat .env | grep "SECRET_KEY\|DB_PASSWORD\|MINIO"

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs
```

#### Step 4: Backup Configuration

```bash
# Backup environment file (SECURE!)
cp .env .env.backup
chmod 600 .env.backup

# Backup SSL certificates
cp -r docker/ssl docker/ssl.backup
```

---

## Verification

### 1. Service Status Check

```bash
# List all containers
docker-compose -f docker-compose.prod.yml ps

# Expected output:
# NAME                             STATUS
# face_attendance_postgres         Up (healthy)
# face_attendance_redis            Up (healthy)
# face_attendance_minio            Up (healthy)
# face_attendance_backend          Up (healthy)
# face_attendance_celery_worker    Up
# face_attendance_celery_beat      Up
# face_attendance_frontend         Up (healthy)
# face_attendance_nginx            Up
```

### 2. API Health Check

```bash
# Check backend API
curl http://localhost/api/v1/health

# Expected response:
# {"status": "ok"}
```

### 3. Frontend Access

```bash
# Test frontend
curl http://localhost/ | head -20

# Should return HTML content
```

### 4. Database Connection

```bash
# Test database
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U postgres -d face_attendance -c "SELECT version();"
```

### 5. Redis Connection

```bash
# Test Redis
docker-compose -f docker-compose.prod.yml exec redis \
  redis-cli ping

# Expected: PONG
```

### 6. MinIO Connection

```bash
# Access MinIO console at http://localhost:9001
# User: minioadmin
# Password: minioadmin123

# Or test via API
curl http://localhost:9000/minio/health/live
```

---

## Troubleshooting

### Common Issues

#### Services Won't Start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs backend

# Common causes:
# 1. Port already in use
netstat -tlnp | grep -E ':(80|8000|5432|6379|9000)'

# 2. Insufficient resources
docker stats

# 3. Permission issues
sudo chown -R $USER:$USER docker/ data/ logs/
```

#### Database Connection Error

```bash
# Check database logs
docker-compose -f docker-compose.prod.yml logs postgres

# Reset database
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml up -d postgres
sleep 30  # Wait for database to initialize
docker-compose -f docker-compose.prod.yml up -d
```

#### Frontend Can't Connect to Backend

```bash
# Check environment variables
docker-compose -f docker-compose.prod.yml exec frontend env | grep VITE

# Verify backend is running
curl http://localhost:8000/api/v1/health

# Check nginx logs
docker-compose -f docker-compose.prod.yml logs nginx

# Check frontend logs
docker-compose -f docker-compose.prod.yml logs frontend
```

#### High Memory/CPU Usage

```bash
# Check resource usage
docker stats

# Check which service is consuming resources
docker-compose -f docker-compose.prod.yml logs <service>

# Restart problematic service
docker-compose -f docker-compose.prod.yml restart <service>

# Or limit resources in docker-compose.prod.yml
```

### Debug Commands

```bash
# Enter service container
docker-compose -f docker-compose.prod.yml exec backend bash

# View real-time logs
docker-compose -f docker-compose.prod.yml logs -f <service>

# Check container health
docker inspect face_attendance_backend | grep -A 10 "Health"

# Test network connectivity
docker-compose -f docker-compose.prod.yml exec backend \
  ping -c 1 postgres

# Check open ports
docker-compose -f docker-compose.prod.yml exec nginx \
  netstat -tlnp
```

---

## Monitoring

### View Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs

# Specific service
docker-compose -f docker-compose.prod.yml logs backend

# Follow logs (real-time)
docker-compose -f docker-compose.prod.yml logs -f

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100

# Timestamped logs
docker-compose -f docker-compose.prod.yml logs --timestamps
```

### Resource Monitoring

```bash
# Real-time resource usage
docker stats

# Specific container
docker stats face_attendance_backend

# Container information
docker inspect face_attendance_backend

# Disk usage
docker system df

# Prune unused resources
docker system prune -a
```

### Service Health

```bash
# Check individual health checks
docker-compose -f docker-compose.prod.yml ps

# Manual health test
docker-compose -f docker-compose.prod.yml exec backend \
  curl http://localhost:8000/api/v1/health

# Database connection test
docker-compose -f docker-compose.prod.yml exec postgres \
  pg_isready -U postgres
```

---

## Scaling

### Horizontal Scaling

```bash
# Scale Celery workers
docker-compose -f docker-compose.prod.yml up -d --scale celery_worker=3

# Scale backend API (with load balancer)
docker-compose -f docker-compose.prod.yml up -d --scale backend=2
# (Requires nginx configuration update)
```

### Vertical Scaling

Edit `docker-compose.prod.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### Performance Tuning

```bash
# PostgreSQL optimization
docker-compose -f docker-compose.prod.yml exec postgres \
  -c shared_buffers=256MB \
  -c effective_cache_size=1GB \
  -c work_mem=16MB

# Redis optimization
docker-compose -f docker-compose.prod.yml exec redis \
  redis-cli CONFIG SET maxmemory 2gb

# Nginx worker optimization
# Edit docker/nginx.conf:
# worker_processes auto;
# worker_connections 2048;
```

---

## Backup & Recovery

### Backup Everything

```bash
# Backup all data
docker-compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U postgres face_attendance > backup.sql

# Backup configurations
tar -czf config_backup.tar.gz .env docker/ docker-compose.prod.yml

# Backup application
tar -czf app_backup.tar.gz . --exclude=data --exclude=logs

# Backup database volume
docker run --rm -v face_attendance_postgres_data:/data \
  -v $(pwd):/backup alpine tar czf /backup/db_volume.tar.gz /data
```

### Restore from Backup

```bash
# Restore database
docker-compose -f docker-compose.prod.yml exec -T postgres \
  psql -U postgres < backup.sql

# Restore configuration
tar -xzf config_backup.tar.gz

# Restart services
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

---

## Maintenance

### Updates

```bash
# Pull latest images
docker pull postgres:16-alpine
docker pull redis:7-alpine
docker pull minio/minio:latest
docker pull nginx:1.27-alpine

# Rebuild custom images
docker-compose -f docker-compose.prod.yml build --pull --no-cache

# Restart services
docker-compose -f docker-compose.prod.yml up -d
```

### Cleanup

```bash
# Remove stopped containers
docker-compose -f docker-compose.prod.yml rm

# Clean unused images
docker image prune -a

# Clean unused volumes
docker volume prune

# Full cleanup
docker system prune -a --volumes
```

### Log Rotation

```bash
# View docker daemon logs config
cat /etc/docker/daemon.json

# Add to /etc/docker/daemon.json:
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}

# Restart docker
sudo systemctl restart docker
```

---

## Advanced Configuration

### Custom Domain (HTTPS)

```bash
# 1. Update .env
ALLOWED_ORIGINS=https://your-domain.com

# 2. Get SSL certificate (Let's Encrypt example)
certbot certonly --standalone -d your-domain.com

# 3. Copy certificates
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem docker/ssl/cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem docker/ssl/key.pem

# 4. Update nginx.conf with your domain
# 5. Uncomment HTTPS section

# 6. Restart
docker-compose -f docker-compose.prod.yml restart nginx
```

### Environment-Specific Overrides

```bash
# Development
docker-compose -f docker-compose.prod.yml \
  -f docker-compose.dev.yml up -d

# Testing
docker-compose -f docker-compose.prod.yml \
  -f docker-compose.test.yml up -d
```

### External PostgreSQL

```yaml
# In docker-compose.prod.yml, modify postgres service:
services:
  postgres:
    image: postgres:16-alpine
    environment:
      # Same as before, but for external database
      # Use external connection string
```

Or just set `DATABASE_URL` environment variable:
```bash
DATABASE_URL=postgresql://user:pass@external-host:5432/dbname
```

---

## Production Checklist

- [ ] All passwords changed from defaults
- [ ] `SECRET_KEY` set to secure random value
- [ ] HTTPS/SSL configured with valid certificate
- [ ] Database backups configured and tested
- [ ] Log aggregation set up
- [ ] Monitoring and alerting configured
- [ ] Firewall rules configured
- [ ] Regular security updates scheduled
- [ ] Disk space monitoring in place
- [ ] Load testing completed
- [ ] Disaster recovery plan documented
- [ ] Health checks verified
- [ ] Backup restoration tested
- [ ] Performance baselines recorded
- [ ] Rate limiting configured

---

## Support & Help

### Useful Commands

```bash
# View all docker resources
docker ps -a
docker volume ls
docker network ls

# Clean all docker resources
docker system prune -a --volumes

# Export/import images
docker save image_name > image.tar
docker load < image.tar

# Docker logs analysis
docker-compose -f docker-compose.prod.yml logs | grep ERROR
```

### Getting Help

1. **Check Logs**: `docker-compose -f docker-compose.prod.yml logs <service>`
2. **Read Documentation**: See related docs in project root
3. **Verify Setup**: Run verification steps above
4. **Check Environment**: Review `.env` configuration
5. **Review Troubleshooting**: See Troubleshooting section

---

## Quick Reference

```bash
# Start
docker-compose -f docker-compose.prod.yml up -d

# Stop
docker-compose -f docker-compose.prod.yml stop

# Restart
docker-compose -f docker-compose.prod.yml restart

# Logs
docker-compose -f docker-compose.prod.yml logs -f

# Status
docker-compose -f docker-compose.prod.yml ps

# Clean everything
docker-compose -f docker-compose.prod.yml down -v
```

---

**Created**: November 5, 2024
**Version**: 1.0.0
**Status**: Production Ready

🐳 **Ready for Docker deployment!**

