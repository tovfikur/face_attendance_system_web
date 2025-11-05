# 🐳 Docker Quick Deployment - Face Attendance System

**Status**: ✅ **READY TO DEPLOY**
**Time to Deploy**: ~5 minutes
**Complexity**: Simple

---

## ⚡ One-Command Deployment

```bash
cd face_attendance_system_web
cp .env.docker .env
docker-compose -f docker-compose.prod.yml up -d
```

**That's it!** Your system is now running.

---

## 📍 Access Your System

```
Frontend:           http://localhost
API:                http://localhost/api/v1
MinIO Console:      http://localhost:9001
Health Check:       http://localhost/health
```

### Default Credentials

| Service | User | Password |
|---------|------|----------|
| Frontend | testuser | testpass123 |
| MinIO | minioadmin | minioadmin123 |

---

## 🔧 What Gets Deployed

```
✅ PostgreSQL Database     (Port 5432)
✅ Redis Cache             (Port 6379)
✅ MinIO Storage           (Port 9000)
✅ Backend API             (Port 8000 - internal)
✅ Celery Worker           (Background tasks)
✅ Celery Beat             (Scheduler)
✅ Frontend React App      (Port 80)
✅ Nginx Reverse Proxy     (Port 80, 443)
```

**Total: 8 services in one command**

---

## 📋 Common Commands

```bash
# View status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop everything
docker-compose -f docker-compose.prod.yml stop

# Restart everything
docker-compose -f docker-compose.prod.yml restart

# Remove everything (cleanup)
docker-compose -f docker-compose.prod.yml down -v

# See specific service logs
docker-compose -f docker-compose.prod.yml logs -f backend
```

---

## ✅ Verify It's Working

```bash
# 1. Check all services are running
docker-compose -f docker-compose.prod.yml ps
# All should show "Up" (or "Up (healthy)")

# 2. Test API
curl http://localhost/api/v1/health
# Should return: {"status": "ok"}

# 3. Test Frontend
curl http://localhost/
# Should return HTML content

# 4. Login
# Open http://localhost in browser
# Login with: testuser / testpass123
```

---

## ⚙️ Configuration (Optional)

All configuration is in `.env` file. Key settings:

```env
# Database
DB_USER=postgres
DB_PASSWORD=postgres123       # Change this!
DB_NAME=face_attendance

# Security
SECRET_KEY=your-secret-key    # Change this!
DEBUG=false

# Frontend
VITE_API_BASE_URL=http://localhost/api
VITE_DEBUG=false
```

For production, update:
1. `DB_PASSWORD` - Strong password
2. `SECRET_KEY` - Generate with: `openssl rand -base64 32`
3. `ALLOWED_ORIGINS` - Your domain
4. `MINIO_ROOT_PASSWORD` - Change from default

---

## 🔒 Production Setup (10 minutes extra)

### Step 1: Secure Environment
```bash
# Edit .env with secure values
nano .env

# Change these:
DB_PASSWORD=YourSecurePassword123!
SECRET_KEY=$(openssl rand -base64 32)
MINIO_ROOT_PASSWORD=YourSecurePassword123!
ALLOWED_ORIGINS=https://your-domain.com
```

### Step 2: Setup HTTPS
```bash
# Copy your SSL certificates
cp /path/to/cert.pem docker/ssl/
cp /path/to/key.pem docker/ssl/

# Update docker/nginx.conf to enable HTTPS
# (Uncomment HTTPS section, add your domain)
```

### Step 3: Deploy
```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🆘 Troubleshooting

### Port Already in Use
```bash
# Find what's using ports
netstat -tlnp | grep -E ':(80|8000|5432|6379)'

# Stop conflicting service or change port in .env
```

### Services Won't Start
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs

# Most common: insufficient resources or permissions
# Try: docker-compose -f docker-compose.prod.yml down -v
#      docker-compose -f docker-compose.prod.yml up -d
```

### Can't Connect to Backend
```bash
# Verify backend is running
docker-compose -f docker-compose.prod.yml logs backend

# Test connectivity
curl http://localhost:8000/api/v1/health

# Restart if needed
docker-compose -f docker-compose.prod.yml restart backend
```

### Database Connection Error
```bash
# Check database logs
docker-compose -f docker-compose.prod.yml logs postgres

# Reset and restart
docker-compose -f docker-compose.prod.yml down -v postgres
docker-compose -f docker-compose.prod.yml up -d postgres
sleep 30
docker-compose -f docker-compose.prod.yml up -d
```

---

## 📊 System Health

```bash
# Real-time resource usage
docker stats

# Check specific container
docker stats face_attendance_backend

# Disk usage
docker system df

# Check if all services are healthy
docker-compose -f docker-compose.prod.yml ps
```

---

## 🔄 Updates

```bash
# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Rebuild with latest code
docker-compose -f docker-compose.prod.yml build --pull --no-cache

# Restart
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🗑️ Cleanup

```bash
# Stop all services
docker-compose -f docker-compose.prod.yml down

# Remove everything including data
docker-compose -f docker-compose.prod.yml down -v

# Remove dangling images
docker image prune -a

# Full cleanup
docker system prune -a --volumes
```

---

## 📖 Next Steps

1. **Read Full Guide**: See `DOCKER_DEPLOYMENT_GUIDE.md`
2. **Configure**: Edit `.env` for your environment
3. **Deploy**: Run the one-command deployment
4. **Verify**: Check everything is working
5. **Test**: Log in and test features
6. **Backup**: Set up automated backups
7. **Monitor**: Monitor system health

---

## 🎯 Success Criteria

You're done when:

- ✅ All 8 services show "Up" status
- ✅ API health check returns 200 OK
- ✅ Frontend loads at http://localhost
- ✅ Can login with testuser/testpass123
- ✅ Real-time features work
- ✅ No errors in logs

---

## 💡 Tips

1. **Use Aliases**: Add to `.bashrc`:
   ```bash
   alias dc='docker-compose -f docker-compose.prod.yml'
   # Then use: dc ps, dc logs, dc restart, etc.
   ```

2. **Monitor in Background**: Keep logs window open
   ```bash
   docker-compose -f docker-compose.prod.yml logs -f
   ```

3. **Quick Restart**: Stop and start without removing data
   ```bash
   docker-compose -f docker-compose.prod.yml restart
   ```

4. **Enter Container**: Debug a service
   ```bash
   docker-compose -f docker-compose.prod.yml exec backend bash
   ```

5. **Check Volumes**: See what data is stored
   ```bash
   docker volume ls
   docker volume inspect face_attendance_postgres_data
   ```

---

## 🚀 That's All!

Your Face Attendance System is now:
- ✅ **Running** in Docker
- ✅ **Fully Integrated** (Frontend + Backend + Database)
- ✅ **Real-time Enabled** (WebSocket)
- ✅ **Production Ready**

**Deployment Time**: ~5 minutes
**No additional setup needed** (optional for production hardening)

Happy deploying! 🎉

---

**See Also**:
- `DOCKER_DEPLOYMENT_GUIDE.md` - Comprehensive guide
- `PROJECT_READY_FOR_DEPLOYMENT.md` - General deployment info
- `.env.docker` - Configuration template
- `docker-compose.prod.yml` - Full Docker Compose setup

