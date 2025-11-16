
FRONTEND INTEGRATION NOTES (updated)
-----------------------------------
1) Real-time updates (SSE)
   - Connect to the SSE endpoint at: GET /api/stream
   - Example JS:
     const evtSource = new EventSource("http://localhost:5000/api/stream");
     evtSource.onmessage = (e) => {
       const data = JSON.parse(e.data);
       // update UI with data.hashrate and data.balance
     };

2) Polling alternative
   - You can poll GET /api/status every few seconds if SSE is not desired.

3) Admin API
   - To request admin token: POST /api/admin/token { "api_key": "<server_api_key>" }
   - To list withdrawals: GET /api/admin/withdrawals with header X-API-KEY: <server_api_key>

4) Wallet backends
   - The backend supports a `wallet_backend` config: simulated | bitcoind | btcpay
   - Edit backend/config.json to set the desired backend and connection details.
   - The included wallet_integration.py contains example stubs for bitcoind RPC and BTCPay.

5) Docker
   - Build and run with: docker-compose up --build
   - Data will persist under ./backend/data (mounted into the container).
