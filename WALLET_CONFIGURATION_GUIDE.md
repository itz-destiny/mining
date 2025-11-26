# Wallet Configuration Guide

## Quick Fix: Use Simulated Mode (Testing)

Your `config.json` has been updated to use **simulated mode** which will work immediately for testing:

```json
{
  "wallet_backend": "simulated"
}
```

**Benefits:**
- ✅ Works immediately, no setup required
- ✅ Generates fake transaction IDs for testing
- ✅ Perfect for development and demos
- ✅ No Bitcoin Core needed

**Limitations:**
- ❌ No real Bitcoin transactions
- ❌ Not for production with real funds

---

## Option 1: Simulated Mode (Current Setting)

**Use Case:** Testing, development, demos

**Configuration:**
```json
{
  "wallet_backend": "simulated"
}
```

**How it works:**
- Withdrawals always succeed
- Returns fake transaction IDs like `sim_tx_abc123...`
- No actual Bitcoin transactions occur

---

## Option 2: Bitcoin Core (Real Payments)

**Use Case:** Production with real Bitcoin transactions

### Prerequisites:
1. **Bitcoin Core installed and running**
2. **RPC enabled** in `bitcoin.conf`
3. **Wallet loaded** with sufficient balance
4. **Correct network** (testnet or mainnet)

### Step 1: Configure Bitcoin Core

Edit `bitcoin.conf` (usually in `~/.bitcoin/` or `%APPDATA%\Bitcoin\`):

```conf
# For Testnet
testnet=1
server=1
rpcuser=your_rpc_username
rpcpassword=your_secure_password
rpcport=18332
rpcallowip=127.0.0.1

# For Mainnet
server=1
rpcuser=your_rpc_username
rpcpassword=your_secure_password
rpcport=8332
rpcallowip=127.0.0.1
```

### Step 2: Start Bitcoin Core

```bash
# Testnet
bitcoind -testnet

# Mainnet
bitcoind
```

### Step 3: Update config.json

```json
{
  "wallet_backend": "bitcoind",
  "bitcoind": {
    "rpc_url": "http://your_rpc_username:your_secure_password@127.0.0.1:18332/"
  }
}
```

**Ports:**
- **Testnet:** `18332`
- **Mainnet:** `8332`

### Step 4: Verify Connection

Test the RPC connection:
```bash
curl --user your_rpc_username:your_secure_password \
  --data-binary '{"jsonrpc":"1.0","id":"test","method":"getblockchaininfo","params":[]}' \
  -H 'content-type: text/plain;' \
  http://127.0.0.1:18332/
```

### Common Issues:

**1. Connection Refused**
- Bitcoin Core not running
- Wrong port number
- Firewall blocking connection

**2. Authentication Failed**
- Wrong RPC username/password
- Credentials don't match `bitcoin.conf`

**3. Insufficient Funds**
- Wallet doesn't have enough BTC
- Check balance: `bitcoin-cli getbalance`

**4. Network Mismatch**
- Address is testnet but Core is mainnet (or vice versa)
- Ensure `testnet=1` in `bitcoin.conf` for testnet

---

## Option 3: BTCPay Server (Future)

**Use Case:** Enterprise payment processing

```json
{
  "wallet_backend": "btcpay",
  "btcpay": {
    "host": "https://your-btcpay-server.com",
    "api_key": "your_api_key"
  }
}
```

**Note:** This is a placeholder implementation. Full BTCPay integration requires additional development.

---

## Switching Between Modes

### To Switch to Simulated:
```json
{
  "wallet_backend": "simulated"
}
```

### To Switch to Bitcoin Core:
```json
{
  "wallet_backend": "bitcoind",
  "bitcoind": {
    "rpc_url": "http://user:pass@127.0.0.1:18332/"
  }
}
```

**Important:** After changing `config.json`, restart your Flask server for changes to take effect.

---

## Security Best Practices

1. **Never commit credentials** to version control
2. **Use environment variables** for production:
   ```bash
   export MINING_SERVER_API_KEY=your_key
   ```
3. **Restrict RPC access** to localhost only
4. **Use strong passwords** for RPC
5. **Use testnet** for development
6. **Backup wallet** regularly

---

## Troubleshooting

### Error: "bitcoind rpc_url not configured"
- Check `config.json` has `bitcoind.rpc_url` set
- Ensure URL format is correct: `http://user:pass@host:port/`

### Error: "Connection refused"
- Bitcoin Core not running
- Wrong port (18332 for testnet, 8332 for mainnet)
- Firewall blocking connection

### Error: "Authentication failed"
- Wrong RPC username/password
- Check `bitcoin.conf` matches config.json

### Error: "Insufficient funds"
- Wallet balance too low
- Use `bitcoin-cli getbalance` to check
- Fund wallet with testnet coins (if testnet)

---

## Current Status

✅ **Your system is now configured for simulated mode**
- Withdrawals will work immediately
- No Bitcoin Core required
- Perfect for testing and development

To switch to real payments later, follow the Bitcoin Core setup steps above.

