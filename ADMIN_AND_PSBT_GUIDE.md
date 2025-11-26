# Admin Interface & PSBT Viewer Guide

## 🔍 Why "Load Miners" and "Load Credits" Show Nothing

**The tables are empty because no shares have been reported yet.**

### How Miners and Credits Are Created

Miners and credits are **only created** when shares are reported via the `/api/report_share` endpoint. This happens when:

1. **Real miners connect** to your pool and submit shares
2. **You use the worker simulator** to test the system
3. **External mining software** reports shares to your pool

### The Flow:

```
Miner/Worker → Reports Shares → /api/report_share → Creates/Updates Miner → Creates Credit Record
```

**Without any share reports, the tables remain empty.**

---

## 📊 Admin Interface Explained

### 1. **Withdrawals Section**
- Shows all withdrawal requests from users
- Status can be: `pending`, `completed`, `error`, `rejected`
- Admin can approve or reject withdrawals
- **This section works** - shows withdrawals from the dashboard

### 2. **Miners Section**
- Lists all miners who have reported shares
- Shows: Miner ID, Balance, Total Shares
- **Empty until shares are reported**

### 3. **Credits Section**
- Lists all credit transactions (when shares were credited)
- Shows: Miner ID, Shares, Amount credited, Date
- **Empty until shares are reported**

### 4. **Get Token Button**
- Generates a JWT token for admin authentication
- Requires the API key to be entered
- Token is saved in browser localStorage

---

## 🧪 How to Test and Create Sample Data

### Option 1: Use the Worker Simulator

```powershell
# From project root
python tools/worker_simulator.py `
  --url http://localhost:5000/api/report_share `
  --secret df09a017ecfd41addee281c8f2b2e652ba2092b74f3f1c286c92f7507 `
  --miner miner1 `
  --workers 3 `
  --shares 100 `
  --interval 2
```

This will:
- Create miner "miner1" with 3 workers
- Report 100 shares every 2 seconds
- Create credit records
- Update miner balance

**After running this, "Load Miners" and "Load Credits" will show data!**

### Option 2: Manual API Call (PowerShell)

```powershell
# Generate HMAC signature
$body = '{"miner_id":"test_miner","worker_name":"worker1","shares":50}'
$secret = "df09a017ecfd41addee281c8f2b2e652ba2092b74f3f1c286c92f7507"
$sig = [System.Convert]::ToHexString([System.Security.Cryptography.HMACSHA256]::new([System.Text.Encoding]::UTF8.GetBytes($secret)).ComputeHash([System.Text.Encoding]::UTF8.GetBytes($body)))

# Send report
Invoke-WebRequest -Uri "http://localhost:5000/api/report_share" `
  -Method POST `
  -Body $body `
  -ContentType "application/json" `
  -Headers @{"X-REPORT-SIG"=$sig}
```

---

## 💰 PSBT Viewer Explained

### What is a PSBT?

**PSBT = Partially Signed Bitcoin Transaction**

A PSBT is used for **offline signing** of Bitcoin transactions. This is a security feature that allows you to:

1. Create a transaction on an online machine
2. Sign it on an offline/air-gapped machine
3. Broadcast it from the online machine

### How It Works in This System

1. **Create PSBT** (`/api/admin/create_psbt`):
   - Admin creates a batch payout for multiple miners
   - System generates an unsigned PSBT
   - PSBT is stored in the database

2. **View PSBT** (PSBT Viewer):
   - Lists all PSBTs in the system
   - Shows: ID, Status, TXID (if broadcast), Created date
   - Click "View PSBT" to see the raw PSBT data
   - Download PSBT for offline signing

3. **Sign PSBT** (Offline):
   - Download the PSBT file
   - Transfer to offline machine
   - Sign using: `bitcoin-cli walletprocesspsbt <psbt>`
   - Or use hardware wallet (HWI)

4. **Finalize PSBT** (`/api/admin/finalize_psbt`):
   - Upload signed PSBT
   - System finalizes and broadcasts the transaction
   - Updates status to "completed"

### PSBT Workflow:

```
Create Batch Payout → Generate PSBT → Download → Sign Offline → Upload Signed → Broadcast
```

### Why Use PSBT?

- **Security**: Private keys never touch the online server
- **Cold Storage**: Sign transactions on air-gapped machines
- **Multi-Sig Support**: Multiple signers can sign the same PSBT
- **Hardware Wallets**: Works with Ledger, Trezor, etc.

---

## 🔧 Admin Interface Features

### API Key Management
- Enter your API key in the "Server API Key" field
- Click "Get Token" to generate a JWT token
- Key is saved in localStorage for future use

### Withdrawal Management
- View all withdrawal requests
- Approve or reject withdrawals
- See transaction IDs for completed withdrawals

### Miner Management
- View all registered miners
- See each miner's balance and share count
- Track miner activity

### Credit Tracking
- View all credit transactions
- See when shares were credited
- Track payout history

---

## 📝 Common Questions

### Q: Why are miners/credits empty?
**A:** No shares have been reported yet. Use the worker simulator to create test data.

### Q: How do I create a PSBT?
**A:** Use the batch payout endpoint or the auto_batch_payout.py tool.

### Q: Can I test without real miners?
**A:** Yes! Use `tools/worker_simulator.py` to simulate miners.

### Q: What's the difference between miners and credits?
**A:** 
- **Miners**: Individual miners with total balance and shares
- **Credits**: Individual credit transactions (each time shares are reported)

### Q: How do I sign a PSBT?
**A:** 
1. Download PSBT from viewer
2. On offline machine: `bitcoin-cli walletprocesspsbt <psbt>`
3. Upload signed PSBT back to system

---

## 🚀 Quick Start: Populate Test Data

1. **Start the server** (if not running)

2. **Run worker simulator:**
   ```powershell
   python tools/worker_simulator.py --url http://localhost:5000/api/report_share --secret df09a017ecfd41addee281c8f2b2e652ba2092b74f3f1c286c92f7507 --miner test_miner --workers 2 --shares 50 --interval 3
   ```

3. **Open Admin Panel:**
   - Go to http://localhost:5000/admin.html
   - Enter API key
   - Click "Load Miners" - should show "test_miner"
   - Click "Load Credits" - should show credit records

4. **Stop simulator** (Ctrl+C) when done testing

---

## 📚 Related Files

- `tools/worker_simulator.py` - Simulate miners reporting shares
- `tools/auto_batch_payout.py` - Automatically create PSBTs for payouts
- `tools/sign_report.py` - Helper to sign and send share reports
- `tools/OFFLINE_SIGNING.md` - Detailed PSBT signing instructions

---

## ✅ Summary

- **Miners/Credits are empty** = No shares reported yet (this is normal!)
- **Use worker simulator** to create test data
- **PSBT Viewer** is for offline transaction signing
- **Admin panel** manages withdrawals, miners, and credits
- **All features work** - they just need data to display!

