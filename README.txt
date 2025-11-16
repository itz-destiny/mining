
Mining PWA - Flask Backend (SIMULATED) - Updated
==============================================

This package now includes:
- SSE realtime endpoint (/api/stream) for frontend to receive live hashrate & balance updates.
- wallet_integration.py: skeleton for integrating with bitcoind JSON-RPC or BTCPay Server.
- Dockerfile + docker-compose.yml for easy containerized deployment.
- Improved admin flow: admin can approve withdrawals which will attempt a payout via configured wallet backend.

IMPORTANT SAFETY & SECURITY NOTES
- This is a demo and **does not** perform real secure wallet management out of the box.
- If you switch to bitcoind or BTCPay backends, secure your RPC credentials and API keys, and run over private networks.
- For production use, add authentication (HTTPS, strong admin tokens), rate-limiting, input validation, logging, and an audited payout process.

How to run (locally)
1. cd backend
2. pip install -r requirements.txt
3. python server.py

How to run with Docker
1. docker-compose up --build
2. the backend will be available on port 5000


Bitcoind integration:
 - Edit backend/config.json and set wallet_backend to 'bitcoind' and provide rpc_url with credentials.
 - Example rpc_url: http://rpcuser:rpcpass@127.0.0.1:8332/
 - Ensure your node has sufficient funds and that RPC account has permission to spend.
 - Test with a small amount first.


--- TESTNET SETUP & TESTING INSTRUCTIONS (Recommended) ---

1) Run a bitcoind testnet node (example):
   - Install Bitcoin Core
   - Start bitcoind in testnet mode:
     bitcoind -testnet -daemon
   - Wait for sync (you can also run a pruned/test setup for quicker testing)

2) Create an RPC user (either via bitcoin.conf or command line):
   - in bitcoin.conf (usually ~/.bitcoin/bitcoin.conf or ~/.bitcoin/testnet3/bitcoin.conf):
     testnet=1
     rpcuser=rpcuser
     rpcpassword=rpcpass
   - Restart bitcoind with the config.

3) Fund your testnet wallet:
   - Use a testnet faucet (search "bitcoin testnet faucet") to send coins to an address from your node:
     bitcoin-cli -testnet getnewaddress
     -> use faucet to send testnet coins
   - Confirm balance with:
     bitcoin-cli -testnet getbalance

4) Configure the backend:
   - Edit backend/config.json in the package. It is preconfigured to use testnet RPC at:
     http://rpcuser:rpcpass@127.0.0.1:18332/
   - If your RPC credentials are different, update them. For security do NOT commit credentials.

5) Run the backend:
   - cd backend
   - pip install -r requirements.txt
   - python server.py
   - Backend will be available at http://127.0.0.1:5000

6) Open the frontend example (served by the backend):
   - Point your browser to http://127.0.0.1:5000/ and host the frontend files (for local testing you can open frontend/index.html directly, but SSE will only work if served from same origin or CORS adjusted)
   - For convenience you can copy frontend files into a simple static server, or modify server.py to serve static files. (This demo expects the frontend to request the same host.)

7) Test withdraw flow (TESTNET):
   - Use the frontend withdraw form to request a testnet withdrawal.
   - The backend will attempt to call `sendtoaddress` on your testnet node. If successful, it will return a txid (spent from your node's wallet).
   - Check tx with: bitcoin-cli -testnet gettransaction <txid>

SAFETY:
- Test on testnet only until you fully validate the flow.
- Never expose RPC credentials publicly.
- For production/mainnet, use a secure secrets store, HTTPS, admin auth, and manual review for large payouts.


--- ADDITIONAL UPDATES: HARDENING & MINING-POOL CREDITING ---

Hardening / Secrets
- The backend now honors environment variable MINING_SERVER_API_KEY for admin auth. Use .env or Docker secrets to inject it.
- A `.env.example` file is included. Do NOT commit real secrets to source control.
- Basic rate limiting is optional and controlled by USE_RATE_LIMIT and RATE_LIMIT_PER_MINUTE env vars.
- Admin endpoints require the X-API-KEY header or api_key query param matching MINING_SERVER_API_KEY.

Mining-pool crediting
- New endpoint: POST /api/report_share
  Body: { "miner_id": "<id>", "worker_name":"...", "shares": <int> }
  This credits the miner's balance using MINING_PAYOUT_RATE_PER_SHARE env var (or config payout_per_share).
- New DB tables: miners, credits. Admin endpoints added to list miners and credits:
  - GET /api/admin/miners
  - GET /api/admin/credits
- Workflow: connect your miners or pool to report shares (or have your pool export share reports to this endpoint). Each reported share is converted to a BTC amount based on the configured payout per share.

Security reminders
- For mainnet use, secure RPC credentials, rotate keys, use HTTPS, and require strong admin authentication (this demo uses a shared API key). Consider OAuth, JWT, or multi-factor admin workflows for production.
- Consider moving payout processing to an offline signer or multi-sig workflow for large amounts.



--- HMAC AUTH FOR POOL REPORTS (ADDED) ---

To securely report shares to the server, the reporting system (your pool or miner gateway) must HMAC-SHA256 the raw request body using the shared secret configured in REPORT_SHARED_SECRET (or report_shared_secret in backend/config.json).

Example (curl + python to generate header):
  BODY='{"miner_id":"miner123","worker_name":"worker1","shares":100}'
  SIG=$(python3 -c "import hmac,hashlib; print(hmac.new(b'change_this_report_secret', b'''$BODY''', hashlib.sha256).hexdigest())")
  curl -X POST http://your-server/api/report_share -H "Content-Type: application/json" -H "X-REPORT-SIG: $SIG" -d "$BODY"

Or example in Python:
  import requests, hmac, hashlib
  secret = b'my_secret_here'
  body = b'{"miner_id":"miner123","worker_name":"worker1","shares":100}'
  sig = hmac.new(secret, body, hashlib.sha256).hexdigest()
  resp = requests.post('http://your-server/api/report_share', headers={'X-REPORT-SIG': sig, 'Content-Type':'application/json'}, data=body)

Make sure the shared secret is kept safe and injected via environment variables or a secrets manager in production.


--- BATCH PAYOUTS & POOL SIGNING TOOL ---

Batch payouts
- Admin endpoint: POST /api/admin/batch_payout
  Body: { "payments": [ { "miner_id":"m1", "to_address":"tb1...", "amount": 0.0001 }, ... ] }
- Admin must call with X-API-KEY header or api_key param (same as other admin endpoints).
- The endpoint will deduct amounts from miners' balances, create withdrawals records, and attempt on-chain payouts via configured wallet backend.

Signing tool for pools
- A helper script is included at tools/sign_report.py to sign and send share reports to the server.
- Example:
    python tools/sign_report.py --secret change_this_report_secret --url http://localhost:5000/api/report_share --miner miner123 --worker w1 --shares 100



--- AUTOMATED BATCH PAYOUTS & OFFLINE SIGNING SUPPORT ADDED ---
Included tools:
 - tools/auto_batch_payout.py (cron-friendly script to create PSBT for eligible miners)
 - tools/sign_report.py (sign & send reports)
 - tools/OFFLINE_SIGNING.md (instructions for offline signing and finalization)
New endpoints:
 - POST /api/admin/create_psbt (admin protected) - create unsigned PSBT
 - POST /api/admin/finalize_psbt (admin protected) - finalize and broadcast signed PSBT


--- PWA & PSBT WEB VIEWER ---
- The backend serves frontend static files at /static/<file> and pages at /index.html, /admin.html, /psbt.html
- The PWA manifest is available at /static/manifest.json and service worker at /static/service-worker.js
- Open http://localhost:5000/index.html to use the PWA. Install via browser install prompt.
- PSBT viewer: http://localhost:5000/psbt.html (admin key required to view PSBTs)
- Worker simulator: tools/worker_simulator.py can simulate miners posting signed share reports.


--- PRODUCTION DEPLOYMENT (SCAFFOLD) ---

This repo includes a production docker-compose scaffold using nginx as a reverse proxy.
Steps (summary):
1. Create a .env file with values: MINING_SERVER_API_KEY, JWT_SECRET, REPORT_SHARED_SECRET, MINING_PAYOUT_RATE_PER_SHARE
2. Configure DNS to point your domain to the host
3. Use Docker Compose (prod) to run containers:
   docker-compose -f docker-compose.prod.yml up --build -d
4. Configure nginx and obtain TLS certs (Let's Encrypt / certbot) for your domain (example nginx config in ./nginx/conf.d/mining.conf).
5. Ensure the backend is only accessible via the proxy and that RPC endpoints to bitcoind are on private network interfaces.

One-command (example, requires env vars and valid domain):
  docker-compose -f docker-compose.prod.yml up --build -d

Security reminders:
- Use a secrets manager for JWT_SECRET, MINING_SERVER_API_KEY, and REPORT_SHARED_SECRET.
- Use firewall rules to restrict direct access to bitcoind RPC.
- Consider using OAuth2 / more robust admin auth in production.
