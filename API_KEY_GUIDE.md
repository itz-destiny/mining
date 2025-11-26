# API Key Guide

## 🔑 How to Get Your API Key

The API key is used to authenticate admin requests. There are **two ways** to set it:

### Option 1: Default API Key (Already Set)

The default API key is already configured in `backend/config.json`:

```json
{
  "server_api_key": "change_this_server_api_key"
}
```

**Default API Key:** `change_this_server_api_key`

You can use this immediately for testing, but **you should change it for production**.

---

### Option 2: Environment Variable (Recommended for Production)

Set the `MINING_SERVER_API_KEY` environment variable. This overrides the config file value.

**Windows PowerShell:**
```powershell
$env:MINING_SERVER_API_KEY = "your_secure_api_key_here"
```

**Windows Command Prompt:**
```cmd
set MINING_SERVER_API_KEY=your_secure_api_key_here
```

**Linux/Mac:**
```bash
export MINING_SERVER_API_KEY=your_secure_api_key_here
```

**Or create a `.env` file in the project root:**
```bash
MINING_SERVER_API_KEY=your_secure_api_key_here
```

---

## 📝 How to Change the API Key

### Method 1: Edit config.json

1. Open `backend/config.json`
2. Change the `server_api_key` value:
   ```json
   {
     "server_api_key": "my_new_secure_key_12345"
   }
   ```
3. Restart the server

### Method 2: Use Environment Variable

Set the environment variable before starting the server (see Option 2 above).

---

## 🎯 How to Use the API Key

### In the Admin Panel (admin.html)

1. Open http://localhost:5000/admin.html
2. Enter your API key in the "Server API Key" field
3. Click "Get Token" (optional - for JWT token)
4. The key will be saved in browser localStorage

**Default key for testing:** `change_this_server_api_key`

### In API Requests

Include the API key in the request header:

```javascript
fetch('/api/admin/miners', {
  headers: {
    'X-API-KEY': 'change_this_server_api_key'
  }
})
```

Or as a query parameter:

```javascript
fetch('/api/admin/miners?api_key=change_this_server_api_key')
```

### Using curl

```bash
curl -H "X-API-KEY: change_this_server_api_key" http://localhost:5000/api/admin/miners
```

---

## 🔒 Security Best Practices

1. **Change the default key immediately** - Never use `change_this_server_api_key` in production
2. **Use a strong, random key** - At least 32 characters, mix of letters, numbers, and symbols
3. **Use environment variables** - Don't commit API keys to version control
4. **Rotate keys regularly** - Change your API key periodically
5. **Restrict access** - Only share the key with trusted administrators

### Generate a Secure API Key

**Python:**
```python
import secrets
print(secrets.token_urlsafe(32))
```

**PowerShell:**
```powershell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})
```

**Online:** Use a password generator to create a 32+ character random string

---

## ✅ Quick Start (Testing)

For immediate testing, use the default key:

1. **Default API Key:** `change_this_server_api_key`
2. Open http://localhost:5000/admin.html
3. Paste `change_this_server_api_key` in the API key field
4. Click "Get Token" or use the key directly

---

## 🛠 Troubleshooting

### "unauthorized" or "invalid api key" error

- Check that you're using the exact key from `config.json` or environment variable
- Make sure there are no extra spaces
- Verify the server is reading the correct key (check server logs)

### Key not working after changing it

- Restart the server after changing `config.json`
- Clear browser localStorage if using the admin panel
- Check that environment variables are set correctly

### Finding your current API key

**Check config.json:**
```powershell
Get-Content backend\config.json | Select-String "server_api_key"
```

**Check environment variable:**
```powershell
$env:MINING_SERVER_API_KEY
```

---

## 📚 Related Endpoints

These endpoints require the API key:

- `GET /api/admin/miners` - List all miners
- `GET /api/admin/credits` - List all credits
- `GET /api/admin/withdrawals` - List withdrawals
- `GET /api/admin/psbts` - List PSBTs
- `POST /api/admin/batch_payout` - Create batch payout
- `POST /api/admin/create_psbt` - Create PSBT
- `POST /api/admin/finalize_psbt` - Finalize PSBT
- `POST /api/admin/process` - Process withdrawal

All require the `X-API-KEY` header with your API key.


