# 🚂 Railway Deployment Guide

## Quick Deploy to Railway

### Step 1: Prepare Your Code

✅ **Already done!** The following files are configured:
- `Dockerfile` - Updated to include frontend
- `railway.json` - Railway configuration
- `.railwayignore` - Files to exclude
- `backend/server.py` - Fixed frontend path detection

### Step 2: Push to GitHub

```bash
git add .
git commit -m "Ready for Railway deployment"
git push origin main
```

### Step 3: Deploy on Railway

1. **Go to Railway**
   - Visit: https://railway.app
   - Sign up with GitHub (free)

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Railway will auto-detect the Dockerfile

3. **Add Environment Variables**
   Click on your service → Variables tab → Add these:

   ```
   MINING_SERVER_API_KEY=your_secure_key_here
   JWT_SECRET=your_jwt_secret_here
   REPORT_SHARED_SECRET=your_hmac_secret_here
   MINING_PAYOUT_RATE_PER_SHARE=0.00000001
   INITIAL_HASHRATE=1000000000000000
   FLASK_ENV=production
   PORT=5000
   ```

   **Important:** `INITIAL_HASHRATE=1000000000000000` sets hashrate to 1000 Th/s

   **Generate secure keys:**
   ```bash
   # Use any of these methods:
   openssl rand -hex 32
   # or
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

4. **Configure Port**
   - Railway automatically sets `PORT` environment variable
   - Your Flask app should use it (already configured)
   - If needed, Railway will map it automatically

5. **Deploy**
   - Railway will automatically build and deploy
   - Watch the build logs
   - Wait for "Deploy successful"

6. **Get Your URL**
   - Click on your service
   - Go to "Settings" → "Domains"
   - Railway provides: `https://your-app.railway.app`
   - Or add a custom domain

### Step 4: Verify Deployment

1. **Check Logs**
   - Go to "Deployments" tab
   - Click on latest deployment
   - Check for errors

2. **Test Your App**
   - Visit: `https://your-app.railway.app`
   - Should see the mining dashboard
   - Test API: `https://your-app.railway.app/api/status`

---

## Troubleshooting

### Issue: "Frontend directory not found"

✅ **Fixed!** The Dockerfile now copies the frontend directory.

If you still see this:
1. Check build logs - ensure frontend is copied
2. Verify `COPY frontend /frontend` in Dockerfile
3. Redeploy

### Issue: Port binding error

Railway automatically handles ports. Make sure:
- `PORT` environment variable is set (Railway sets this automatically)
- Your app listens on `0.0.0.0` (already configured)

### Issue: Build fails

**Check:**
1. Dockerfile syntax is correct
2. `requirements.txt` exists in backend/
3. All files are committed to Git
4. Check build logs for specific errors

### Issue: App crashes on startup

**Check logs:**
1. Go to Railway dashboard
2. Click on your service
3. View "Logs" tab
4. Look for error messages

**Common fixes:**
- Verify all environment variables are set
- Check database path (should be `/app/data/`)
- Ensure frontend files are accessible

---

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `MINING_SERVER_API_KEY` | ✅ Yes | Admin API key | `abc123...` |
| `JWT_SECRET` | ✅ Yes | JWT token secret | `secret123...` |
| `REPORT_SHARED_SECRET` | ✅ Yes | HMAC secret for shares | `secret456...` |
| `MINING_PAYOUT_RATE_PER_SHARE` | ⚠️ Optional | Payout rate | `0.00000001` |
| `FLASK_ENV` | ⚠️ Optional | Environment | `production` |
| `PORT` | ❌ Auto | Port (Railway sets this) | `5000` |

---

## Updating Your App

Railway auto-deploys when you push to GitHub:

```bash
git add .
git commit -m "Update app"
git push origin main
```

Railway will:
1. Detect the push
2. Rebuild the Docker image
3. Deploy the new version
4. Keep old version running until new one is ready

---

## Free Tier Limits

Railway free tier includes:
- ✅ 500 hours/month compute time
- ✅ $5 credit/month
- ✅ Unlimited deployments
- ✅ HTTPS included
- ✅ Custom domains

**Note:** Free tier is perfect for demos and small projects!

---

## Custom Domain (Optional)

1. Go to your service → Settings → Domains
2. Click "Generate Domain" or "Custom Domain"
3. For custom domain:
   - Add your domain
   - Follow DNS setup instructions
   - Railway handles SSL automatically

---

## Monitoring

**View Logs:**
- Real-time logs in Railway dashboard
- Filter by deployment
- Search logs

**Metrics:**
- CPU usage
- Memory usage
- Network traffic
- Request count

---

## Success Checklist

- [ ] Code pushed to GitHub
- [ ] Railway project created
- [ ] Environment variables set
- [ ] Build successful
- [ ] App accessible at Railway URL
- [ ] Frontend loads correctly
- [ ] API endpoints working
- [ ] No errors in logs

---

## Your App URL

Once deployed, your app will be available at:
```
https://your-app-name.railway.app
```

**Share this link** - anyone can access your mining pool dashboard!

---

## Need Help?

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Check build logs for specific errors
- Verify all environment variables are set

---

**🎉 Your mining pool is now live on Railway!**

