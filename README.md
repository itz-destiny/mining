[![Release](https://img.shields.io/badge/release-v1.0.0-blue.svg)](https://github.com/USERNAME/REPO/releases)


# Mining PWA Backend (Bitcoin Testnet/Mainnet Ready)

A full-featured, production-oriented **Bitcoin mining backend + PWA frontend**, including:

- ⚡ Real BTC payouts (bitcoind RPC)
- 📡 Mining-pool share crediting with HMAC authentication
- 🧾 PSBT offline signing and batch payouts
- 📱 Progressive Web App (installable on iOS/Android)
- 🔐 JWT user accounts + miner linking
- 📊 Live hashrate dashboard (Chart.js)
- 🐳 Docker & Nginx deployment scaffold
- 🛡 Security‑focused architecture
- 🤖 Worker simulator for testing
- 🚀 GitHub CI and Release workflow

---

## 📐 Architecture Overview

```
Workers → HMAC Share Reports → Backend → Credits DB → Batch Payout → PSBT → Offline Signer → Broadcast
                                              ↑
                          PWA Dashboard (SSE) + Admin Panel + JWT Auth
```

---

## ✨ Features

### 🔒 Security & Wallet Handling
- Offline PSBT signing support  
- Bitcoind JSON-RPC integration  
- Protected admin endpoints with API key  
- HMAC-secured pool share reporting  
- JWT user identity & miner linking  

### 🛠 Mining Logic
- Report shares via `/api/report_share`  
- Automatic crediting using payout_per_share  
- Batch payout creation  
- PSBT generation + finalization  
- Supports both **testnet** and **mainnet**  

### 📱 PWA Frontend
- Installable from Safari/Chrome  
- Live hashrate SSE updates  
- User dashboard + miner linking  
- Admin interface + PSBT viewer  

---

## 🚀 Deployment (Production)

### 1. Create `.env`:
```
MINING_SERVER_API_KEY=your_admin_key
JWT_SECRET=your_jwt_secret
REPORT_SHARED_SECRET=your_hmac_secret
MINING_PAYOUT_RATE_PER_SHARE=0.00000001
```

### 2. Build & run:
```
docker-compose -f docker-compose.prod.yml up --build -d
```

### 3. Configure Nginx (included)
- TLS recommended with Certbot  
- Protect `bitcoind` RPC via firewall  

---

## 🔐 Offline PSBT Signing

1. Create batch payout:
```
POST /api/admin/create_psbt
```
2. Download PSBT via `/psbt.html`
3. Move PSBT to offline machine
4. Sign using:
```
bitcoin-wallet processpsbt ...
```
or hardware wallet (HWI)
5. Upload signed PSBT:
```
POST /api/admin/finalize_psbt
```

---

## 🤖 Worker Simulator (testing)
Run:
```
python tools/worker_simulator.py --url http://localhost:5000/api/report_share   --secret YOUR_SECRET --miner miner1 --workers 5 --shares 20 --interval 3
```

---

## 📦 GitHub Release Automation

GitHub Action:
- Runs on push  
- Packages ZIP release  
- Performs lint  
- Builds docker image (optional toggle)  

Workflow file included in `.github/workflows/release.yml`.

---

## 🧭 Repository Structure

```
backend/      → Flask app, wallet integration, DB
frontend/     → PWA, dashboard, admin panel
tools/        → worker simulator, PSBT helpers
nginx/        → production reverse proxy config
.github/      → CI & release pipelines
```

---

## 🪙 Donation (testnet)
If you want to test payouts:
```
tb1qexampleaddressxxxxxxxxxxxxxxxxxxxxxx
```

---

## 📄 License
MIT License

---

## Maintainer Notes
This project is production-ready **with correct security hardening**.  
Review firewall, RPC lock-down, TLS & secret rotation before mainnet enablement.



## 📸 Screenshots (placeholders)

![Dashboard](docs/images/dashboard.png)
![Admin Panel](docs/images/admin.png)
![PSBT Viewer](docs/images/psbt.png)



--- STRATUM RELAY / MINING PROXY (FEATURE) ---

A minimal Stratum-compatible server (educational) has been added at `backend/stratum_server.py`.
This allows ASIC miners or mining software to connect using a basic JSON-RPC-over-TCP protocol and submit shares.
Key notes:
- Start the server: `python backend/stratum_server.py` (requires network access to your backend and correct REPORT_SHARED_SECRET)
- The Stratum server issues simple simulated jobs and forwards share reports to the backend's `/api/report_share` endpoint using the HMAC secret.
- For production, prefer well-tested pool software. This module is a relay/simulator to help integrate miners with the crediting system.

Example miner connection (cgminer/bfgminer config) to point to the proxy:
```
--url=http://your-proxy-host:3333 --userpass=miner1:password
```

Testing quick flow:
1. Start backend (python backend/server.py).
2. Start stratum server (python backend/stratum_server.py).
3. Run example client: `python tools/example_stratum_client.py --worker miner1`
4. Check admin miners page to see credited shares/balance.

Security reminder: Use TLS, firewall rules, and authenticated pool connectors in production. Do not expose RPC or admin endpoints publicly without protection.



---

## Stratum Async Server

A production-oriented asyncio Stratum server skeleton has been added at `backend/stratum_async.py`.

- It polls `getblocktemplate` from your bitcoind RPC and broadcasts jobs to connected miners.
- TLS is supported (configure cert/key in backend/config.json `stratum_async.tls_cert`/`tls_key`).
- Worker credentials can be provided via `stratum_async.auth_map` in `backend/config.json`.

Commands:
```
python backend/stratum_async.py
```

Security note: This is still a simplified implementation. Use a battle-tested pool implementation for high-volume production.


---

## Full Job Assembly, TLS Automation & Production Hardening

The project now includes a job assembler module (`backend/stratum_job_assembler.py`) used by the async stratum server to construct coinbase, merkle root, and block header fields from `getblocktemplate`.

TLS automation: `docker-compose.certbot.yml` + nginx challenge config are provided to obtain/renew Let's Encrypt certs. You must mount `./nginx/certs` and ensure DNS points to your server.

Production hardening checklist is available in `PRODUCTION_HARDENING.md`.



--- SYSTEMD INSTALLER ---
A helper script `install_systemd_units.sh` is included in the project root.
Run it on your server as root to install, enable, and start the `mining-backend` and `mining-stratum` services:
  sudo ./install_systemd_units.sh
Please review and edit the unit files (`mining-backend.service`, `mining-stratum.service`) first to ensure the `User=` and paths match your system.
"# mining" 
