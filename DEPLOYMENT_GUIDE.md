# 🚀 Deployment Guide: Push Your Mining Pool Online

## ✅ Hashrate Configuration

Your hashrate is **already set to 1000 TH/s** in `backend/config.json`:
```json
"initial_hashrate": 1000000000000000  // 1,000,000,000,000,000 H/s = 1000 TH/s
```

You can also change it via API after deployment:
```bash
POST /api/set_hashrate
{
  "hashrate": 1000000000000000
}
```

---

## 🐳 Is Docker Free?

**YES! Docker is completely free to use:**

1. **Docker Engine** (for Linux servers) - Open source and free
2. **Docker Desktop** (for Windows/Mac) - Free for personal use, small businesses, education, and open-source projects
3. **Docker Compose** - Free and open source

**No credit card required.** You only pay if you use Docker's enterprise/cloud services (which you don't need for this project).

---

## 📋 Prerequisites

Before deploying, you need:
1. **A server** (VPS/cloud instance) with:
   - Ubuntu 20.04+ or similar Linux
   - At least 2GB RAM
   - Docker and Docker Compose installed
   - Domain name (optional, but recommended for HTTPS)

2. **Popular hosting options** (all support Docker):
   - **DigitalOcean** - $6/month (Droplet)
   - **Linode** - $5/month
   - **Vultr** - $6/month
   - **AWS EC2** - Pay as you go
   - **Google Cloud** - Free tier available
   - **Azure** - Free tier available

---

## 🚀 Step-by-Step Deployment

### Step 1: Prepare Your Server

SSH into your server and install Docker:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose -y

# Add your user to docker group (optional, to run without sudo)
sudo usermod -aG docker $USER
newgrp docker
```

### Step 2: Upload Your Project

**Option A: Using Git (Recommended)**
```bash
# On your server
cd ~
git clone <your-repo-url>
cd mining_pwa_backend_flask_with_systemd_and_smoke_install
```

**Option B: Using SCP (from your local machine)**
```bash
# From your Windows machine (PowerShell)
scp -r . user@your-server-ip:/home/user/mining-pool
```

**Option C: Using SFTP/FTP client**
- Use FileZilla, WinSCP, or similar
- Upload entire project folder

### Step 3: Create Environment File

On your server, create a `.env` file in the project root:

```bash
cd ~/mining_pwa_backend_flask_with_systemd_and_smoke_install
nano .env
```

Add these variables (generate secure random strings):
```env
MINING_SERVER_API_KEY=your_secure_random_key_here
JWT_SECRET=your_jwt_secret_here
REPORT_SHARED_SECRET=your_hmac_secret_here
MINING_PAYOUT_RATE_PER_SHARE=0.00000001
FLASK_ENV=production
```

**Generate secure keys:**
```bash
# Generate random keys
openssl rand -hex 32
```

### Step 4: Configure Nginx (Optional but Recommended)

Edit `nginx/conf.d/mining.conf` to set your domain:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    location / {
        proxy_pass http://mining-backend:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Step 5: Build and Deploy

```bash
# Build and start containers
docker-compose -f docker-compose.prod.yml up --build -d

# Check if containers are running
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Step 6: Set Up HTTPS (Optional but Recommended)

If you have a domain, set up Let's Encrypt SSL:

```bash
# Use the certbot compose file
docker-compose -f docker-compose.certbot.yml up -d
```

---

## 🌐 Access Your Pool

Once deployed:

- **HTTP:** `http://your-server-ip` or `http://your-domain.com`
- **HTTPS:** `https://your-domain.com` (after SSL setup)

**Test endpoints:**
- Dashboard: `http://your-server-ip/`
- API Status: `http://your-server-ip/api/status`
- Admin Panel: `http://your-server-ip/admin.html`

---

## 🔧 Useful Commands

```bash
# Stop the pool
docker-compose -f docker-compose.prod.yml down

# Restart the pool
docker-compose -f docker-compose.prod.yml restart

# View logs
docker-compose -f docker-compose.prod.yml logs -f mining-backend

# Update code and redeploy
git pull  # or upload new files
docker-compose -f docker-compose.prod.yml up --build -d

# Set hashrate via API (after deployment)
curl -X POST http://your-server-ip/api/set_hashrate \
  -H "Content-Type: application/json" \
  -d '{"hashrate": 1000000000000000}'
```

---

## 🔒 Security Checklist

Before going live:

- [ ] Change all default secrets in `.env`
- [ ] Set up firewall (only allow ports 80, 443, 3333)
- [ ] Use HTTPS with Let's Encrypt
- [ ] Restrict admin endpoints to specific IPs (in nginx config)
- [ ] Keep Docker and system updated
- [ ] Use strong passwords for bitcoind RPC (if using real wallet)

---

## 📊 Verify Deployment

1. **Check API status:**
   ```bash
   curl http://your-server-ip/api/status
   ```

2. **Check hashrate:**
   ```bash
   curl http://your-server-ip/api/status | grep hashrate
   ```

3. **Access dashboard in browser:**
   - Open `http://your-server-ip/`
   - Should show "1000 TH/s" hashrate

---

## 🆘 Troubleshooting

**Containers won't start:**
```bash
docker-compose -f docker-compose.prod.yml logs
```

**Port already in use:**
```bash
# Check what's using port 80
sudo lsof -i :80
# Or change ports in docker-compose.prod.yml
```

**Can't access from browser:**
- Check firewall: `sudo ufw allow 80/tcp`
- Check nginx config: `docker-compose logs nginx`
- Verify containers are running: `docker ps`

---

## 💡 Quick Deploy Script

Save this as `deploy.sh` on your server:

```bash
#!/bin/bash
cd ~/mining_pwa_backend_flask_with_systemd_and_smoke_install
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up --build -d
echo "Deployment complete! Check logs with: docker-compose -f docker-compose.prod.yml logs -f"
```

Make it executable:
```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 📝 Notes

- **Hashrate is already set to 1000 TH/s** in config.json
- Docker is **100% free** for this use case
- The pool will be accessible at your server's IP or domain
- All data persists in `./backend/data/` directory
- For production, consider using a managed database instead of SQLite

---

**Your mining pool is now online! 🎉**

