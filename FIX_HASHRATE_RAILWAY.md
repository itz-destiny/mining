# 🔧 Fix Hashrate on Railway (800 H/s → 1000 Th/s)

## Quick Fix: Add Environment Variable

Your Railway deployment is showing **800 H/s** instead of **1000 Th/s**. Here's how to fix it:

### Step 1: Go to Railway Dashboard

1. Visit: https://railway.app
2. Click on your project: **mining-production**
3. Click on your service

### Step 2: Add Environment Variable

1. Click on **"Variables"** tab
2. Click **"+ New Variable"**
3. Add:
   - **Name:** `INITIAL_HASHRATE`
   - **Value:** `1000000000000000`
4. Click **"Add"**

### Step 3: Redeploy

Railway will automatically redeploy when you add the variable. Or:

1. Go to **"Deployments"** tab
2. Click **"Redeploy"** (three dots menu)

### Step 4: Verify

1. Wait for deployment to complete (green checkmark)
2. Visit: `https://mining-production-e439.up.railway.app`
3. Should now show: **1000Th/s** ✅

---

## Alternative: Use API to Set Hashrate

If you prefer, you can also set it via API after deployment:

```bash
curl -X POST https://mining-production-e439.up.railway.app/api/set_hashrate \
  -H "Content-Type: application/json" \
  -d '{"hashrate": 1000000000000000}'
```

But using the environment variable is better because it persists across restarts.

---

## Why This Happened

The default hashrate in the code is **800 H/s**. Even though your `config.json` has the correct value (`1000000000000000`), Railway might be:
- Using a fresh config
- Not reading the config.json file properly
- Using environment variables instead

**Solution:** Set `INITIAL_HASHRATE` environment variable to override the default.

---

## Environment Variable Reference

| Variable | Value | Description |
|----------|-------|-------------|
| `INITIAL_HASHRATE` | `1000000000000000` | Sets hashrate to 1000 Th/s (1,000,000,000,000,000 H/s) |

**Hashrate Values:**
- `1000000000000000` = 1000 Th/s ✅
- `1000000000000` = 1 Th/s
- `1000000000` = 1 Gh/s
- `800` = 800 H/s (default)

---

## After Adding the Variable

1. ✅ Railway will auto-redeploy
2. ✅ Wait for "Deploy successful"
3. ✅ Visit your URL
4. ✅ Should show **1000Th/s** now!

---

**Your URL:** `https://mining-production-e439.up.railway.app`

After adding the environment variable and redeploying, the hashrate should display correctly! 🚀

