# How to Run the Worker Simulator

The worker simulator creates fake miners that report shares to your pool, allowing you to test the system and populate data.

---

## 🚀 Quick Start

### Basic Command

```powershell
python tools/worker_simulator.py `
  --url http://localhost:5000/api/report_share `
  --secret df09a017ecfd41addee281c8f2b2e652ba2092b74f3f1c286c92f7507 `
  --miner test_miner `
  --workers 3 `
  --shares 50 `
  --interval 5
```

### What This Does

- **`--url`**: The API endpoint for reporting shares
- **`--secret`**: Your HMAC secret (from `config.json` → `report_secret`)
- **`--miner`**: Miner ID (e.g., "miner1", "test_miner")
- **`--workers`**: Number of worker threads (simulates multiple mining rigs)
- **`--shares`**: Number of shares to report each time
- **`--interval`**: Seconds between reports (with random variation)

---

## 📋 Step-by-Step Instructions

### 1. Make Sure Server is Running

```powershell
cd backend
python server.py
```

Keep this running in one terminal.

### 2. Open New Terminal

Open a **new PowerShell window** (keep server running).

### 3. Run Simulator

```powershell
# Navigate to project root
cd "C:\Users\pc\Documents\Mr. Bishop\mining_pwa_backend_flask_with_systemd_and_smoke_install"

# Run simulator
python tools/worker_simulator.py `
  --url http://localhost:5000/api/report_share `
  --secret df09a017ecfd41addee281c8f2b2e652ba2092b74f3f1c286c92f7507 `
  --miner miner1 `
  --workers 5 `
  --shares 100 `
  --interval 3
```

### 4. Watch It Work

You should see output like:
```
worker1 200 {"ok":true,"miner_id":"miner1","credited":0.00000001,"shares":100}
worker2 200 {"ok":true,"miner_id":"miner1","credited":0.00000001,"shares":100}
worker3 200 {"ok":true,"miner_id":"miner1","credited":0.00000001,"shares":100}
```

### 5. Check Admin Panel

1. Open http://localhost:5000/admin.html
2. Enter API key: `df09a017ecfd41addee281c8f2b2e652ba2092b74f3f1c286c92f7507`
3. Click "Load Miners" - you should see "miner1" with balance
4. Click "Load Credits" - you should see credit records

### 6. Stop Simulator

Press **Ctrl+C** in the simulator terminal to stop.

---

## 🎯 Example Scenarios

### Scenario 1: Single Miner, Slow Reports
```powershell
python tools/worker_simulator.py `
  --url http://localhost:5000/api/report_share `
  --secret df09a017ecfd41addee281c8f2b2e652ba2092b74f3f1c286c92f7507 `
  --miner slow_miner `
  --workers 1 `
  --shares 10 `
  --interval 10
```
- 1 worker
- Reports 10 shares every 10 seconds
- Good for testing basic functionality

### Scenario 2: Multiple Miners, Fast Reports
```powershell
python tools/worker_simulator.py `
  --url http://localhost:5000/api/report_share `
  --secret df09a017ecfd41addee281c8f2b2e652ba2092b74f3f1c286c92f7507 `
  --miner fast_miner `
  --workers 10 `
  --shares 1000 `
  --interval 2
```
- 10 workers
- Reports 1000 shares every 2 seconds
- Simulates high-volume mining

### Scenario 3: Multiple Different Miners
Run multiple instances with different miner IDs:

**Terminal 1:**
```powershell
python tools/worker_simulator.py --url http://localhost:5000/api/report_share --secret df09a017ecfd41addee281c8f2b2e652ba2092b74f3f1c286c92f7507 --miner miner1 --workers 3 --shares 50 --interval 5
```

**Terminal 2:**
```powershell
python tools/worker_simulator.py --url http://localhost:5000/api/report_share --secret df09a017ecfd41addee281c8f2b2e652ba2092b74f3f1c286c92f7507 --miner miner2 --workers 2 --shares 75 --interval 4
```

---

## 🔍 Understanding the Output

### Success Response
```
worker1 200 {"ok":true,"miner_id":"miner1","credited":0.00000001,"shares":100}
```
- `200` = HTTP success
- `credited` = BTC amount credited to miner
- `shares` = Number of shares reported

### Error Response
```
worker1 401 {"ok":false,"error":"invalid signature"}
```
- `401` = Authentication failed
- Check that `--secret` matches your config

---

## ⚙️ Configuration

### Find Your Secret

Check `backend/config.json`:
```json
{
  "stratum_async": {
    "report_secret": "df09a017ecfd41addee281c8f2b2e652ba2092b74f3f1c286c92f7507"
  }
}
```

Or use environment variable:
```powershell
$env:REPORT_SHARED_SECRET = "your_secret_here"
```

### Parameters Explained

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--url` | API endpoint | `http://localhost:5000/api/report_share` |
| `--secret` | HMAC secret | From `config.json` |
| `--miner` | Miner ID | `miner1`, `test_miner`, etc. |
| `--workers` | Number of workers | `1` to `10` (or more) |
| `--shares` | Shares per report | `10`, `100`, `1000` |
| `--interval` | Seconds between reports | `3`, `5`, `10` |

---

## 🐛 Troubleshooting

### Error: "invalid signature"
- **Problem**: Secret doesn't match
- **Fix**: Check `config.json` → `report_secret` value
- **Verify**: Use the exact secret from your config

### Error: "Connection refused"
- **Problem**: Server not running
- **Fix**: Start the server first: `cd backend && python server.py`

### Error: "Module not found: requests"
- **Problem**: Missing Python dependency
- **Fix**: `pip install requests`

### No data in Admin Panel
- **Problem**: Simulator not running or errors
- **Fix**: 
  1. Check simulator output for errors
  2. Verify secret is correct
  3. Make sure server is running
  4. Wait a few seconds for reports to accumulate

---

## 📊 What Happens When You Run It

1. **Simulator starts** → Creates worker threads
2. **Each worker** → Reports shares periodically
3. **Backend receives** → Validates HMAC signature
4. **If valid** → Creates/updates miner record
5. **Credits miner** → Adds balance based on shares
6. **Creates credit record** → Tracks the transaction
7. **Admin panel** → Shows miners and credits

---

## 💡 Tips

1. **Start Small**: Begin with 1 worker, 10 shares, 5 second interval
2. **Watch Balance**: Check admin panel to see balance increase
3. **Multiple Miners**: Run multiple instances for different miners
4. **Stop Gracefully**: Use Ctrl+C to stop (it will finish current reports)

---

## 🎯 Quick Reference

**Your Current Secret:**
```
df09a017ecfd41addee281c8f2b2e652ba2092b74f3f1c286c92f7507
```

**Quick Command (Copy & Paste):**
```powershell
python tools/worker_simulator.py --url http://localhost:5000/api/report_share --secret df09a017ecfd41addee281c8f2b2e652ba2092b74f3f1c286c92f7507 --miner test_miner --workers 3 --shares 50 --interval 3
```

---

## ✅ Success Checklist

After running the simulator:
- [ ] Simulator shows "200" responses
- [ ] Admin panel shows miners when you click "Load Miners"
- [ ] Admin panel shows credits when you click "Load Credits"
- [ ] Miner balance increases over time
- [ ] No errors in simulator output

---

**That's it!** Run the simulator to populate your pool with test data. 🚀

