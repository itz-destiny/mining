# Withdrawal Error Explanation

## Why Withdrawals Show "ERROR" Status

The withdrawal error occurs when an admin **approves** a withdrawal request, but the payment processing fails. Here's what happens:

### Error Flow:
1. User creates withdrawal request → Status: `pending`
2. Admin clicks "✓ Approve" → System attempts payment
3. Payment fails → Status changes to `error`

### Common Causes:

1. **Wallet Backend Not Configured**
   - If `wallet_backend` is set to `"bitcoind"` but RPC URL is missing
   - Error: `"bitcoind rpc_url not configured"`

2. **Bitcoin Core RPC Connection Failed**
   - Bitcoin Core not running
   - Wrong RPC credentials
   - Network connectivity issues
   - RPC port blocked by firewall

3. **Insufficient Wallet Balance**
   - Wallet doesn't have enough BTC to cover the withdrawal
   - Transaction would fail due to low balance

4. **Invalid Address Format**
   - Address doesn't match network (testnet vs mainnet)
   - Malformed address string

5. **Unknown Wallet Backend**
   - `wallet_backend` set to unsupported value
   - Error: `"unknown wallet backend"`

### How to Fix:

#### For Simulated Mode (Testing):
```json
{
  "wallet_backend": "simulated"
}
```
This will always succeed with fake transaction IDs.

#### For Real Bitcoin Core:
```json
{
  "wallet_backend": "bitcoind",
  "bitcoind": {
    "rpc_url": "http://rpcuser:rpcpass@127.0.0.1:18332/"
  }
}
```

**Requirements:**
- Bitcoin Core must be running
- RPC credentials must be correct
- Wallet must have sufficient balance
- Network must match (testnet vs mainnet)

### Error Logging:
Errors are now logged to the server log with details:
```
Withdrawal {id} failed: {error_message}
```

Check your server logs (`mining_backend.log` or console output) for specific error details.

---

## Professional Color Scheme Update

The color palette has been updated to a **mature, professional corporate style**:

### Old Colors (Bright Purple):
- Primary: `#667eea` (Bright Purple)
- Secondary: `#764ba2` (Violet)

### New Colors (Professional Navy):
- Primary: `#1e3a5f` (Deep Navy Blue)
- Primary Dark: `#152a47` (Darker Navy)
- Secondary: `#2c5282` (Medium Blue)
- Accent: `#2563eb` (Bright Blue)

### Status Colors (Professional):
- Success: `#10b981` (Professional Green)
- Danger: `#ef4444` (Professional Red)
- Warning: `#f59e0b` (Amber)
- Info: `#3b82f6` (Info Blue)

The new color scheme provides:
- ✅ More professional, corporate appearance
- ✅ Better readability and contrast
- ✅ Mature, trustworthy aesthetic
- ✅ Better for business/production environments

