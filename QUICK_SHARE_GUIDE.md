# 🚀 Quick Guide: Share Your App as a Link

## Option 1: Quick Testing (Free - No Server Needed)

### Using ngrok (Easiest)

**Step 1: Install ngrok**
- Download from: https://ngrok.com/download
- Or use: `choco install ngrok` (Windows) or `brew install ngrok` (Mac)

**Step 2: Start your Flask server**
```bash
cd backend
python server.py
```
Server should be running on `http://localhost:5000`

**Step 3: Create public tunnel**
```bash
ngrok http 5000
```

**Step 4: Share the link!**
ngrok will give you a URL like:
```
https://abc123.ngrok.io
```

**Share this link** - anyone can access your app!

**Limitations:**
- Free tier: URL changes each time you restart
- Free tier: Limited connections
- Perfect for testing/demos

---

### Using localtunnel (Alternative)

**Step 1: Install**
```bash
npm install -g localtunnel
```

**Step 2: Start tunnel**
```bash
lt --port 5000
```

**Step 3: Share the link!**
You'll get a URL like: `https://random-name.loca.lt`

---

## Option 2: Deploy to Free Hosting (Permanent Link)

### Railway (Recommended - Free Tier)

**Step 1: Sign up**
- Go to: https://railway.app
- Sign up with GitHub (free)

**Step 2: Create new project**
- Click "New Project"
- Select "Deploy from GitHub repo"
- Connect your repository

**Step 3: Configure**
- Railway auto-detects Docker
- Add environment variables in dashboard:
  ```
  MINING_SERVER_API_KEY=your_key
  JWT_SECRET=your_secret
  REPORT_SHARED_SECRET=your_secret
  FLASK_ENV=production
  ```

**Step 4: Deploy**
- Railway builds automatically
- Get permanent URL: `https://your-app.railway.app`

**Free tier includes:**
- ✅ 500 hours/month free
- ✅ Permanent URL
- ✅ HTTPS included
- ✅ Auto-deploy from Git

---

### Render (Alternative)

**Step 1: Sign up**
- Go to: https://render.com
- Sign up (free)

**Step 2: Create Web Service**
- New → Web Service
- Connect GitHub repo
- Build command: `docker-compose -f docker-compose.prod.yml build`
- Start command: `docker-compose -f docker-compose.prod.yml up`

**Step 3: Get URL**
- Render provides: `https://your-app.onrender.com`

**Free tier:**
- ✅ Free SSL
- ✅ Auto-deploy
- ⚠️ Spins down after 15 min inactivity (free tier)

---

### Fly.io (Another Option)

**Step 1: Install flyctl**
```bash
# Windows (PowerShell)
iwr https://fly.io/install.ps1 -useb | iex
```

**Step 2: Sign up & deploy**
```bash
fly auth signup
fly launch
```

**Step 3: Share URL**
- Get: `https://your-app.fly.dev`

---

## Option 3: Deploy to VPS (Full Control)

See `DEPLOYMENT_GUIDE.md` for complete instructions.

**Quick steps:**
1. Get VPS (DigitalOcean, Linode, etc.)
2. Install Docker
3. Upload project
4. Run: `docker-compose -f docker-compose.prod.yml up -d`
5. Get your server IP or domain

---

## Fixing the Withdrawal Error

The error is showing because an old withdrawal record has "error" status. Here's how to fix:

### Option A: Restart Server (Easiest)
1. Stop your Flask server (Ctrl+C)
2. Start it again: `python backend/server.py`
3. New withdrawals will work with simulated mode

### Option B: Clear Old Error (If you have database access)
The old error withdrawal is stored in `backend/data/withdrawals.db`. You can:
- Delete the database file (will clear all withdrawals)
- Or manually update the status in the database

### Option C: Approve the Error Withdrawal Again
1. Go to Admin Panel
2. Find the error withdrawal
3. Click "✓ Approve" again
4. It should work now with simulated mode

---

## Recommended: Railway (Easiest Permanent Solution)

**Why Railway:**
- ✅ Free tier (500 hours/month)
- ✅ Permanent URL
- ✅ HTTPS included
- ✅ Auto-deploy from Git
- ✅ No credit card needed
- ✅ Easy setup

**Time to deploy:** ~5 minutes

1. Push code to GitHub
2. Connect Railway to GitHub
3. Add environment variables
4. Deploy
5. Share link!

---

## Quick Comparison

| Method | Cost | Setup Time | Permanent URL | Best For |
|--------|------|------------|----------------|----------|
| ngrok | Free | 2 min | ❌ Changes | Quick testing |
| Railway | Free | 5 min | ✅ Yes | Demos, sharing |
| Render | Free | 5 min | ✅ Yes | Demos |
| VPS | $5-6/mo | 30 min | ✅ Yes | Production |

---

**Need help?** Check `DEPLOYMENT_GUIDE.md` for detailed instructions.

