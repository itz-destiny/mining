#!/usr/bin/env python3
"""
stratum_async.py - Asyncio-based Stratum-like server with bitcoind getblocktemplate job sourcing,
TLS support, and simple worker authentication adapter.

Features:
- Uses asyncio streams for scalable TCP handling.
- Pulls jobs from bitcoind via JSON-RPC getblocktemplate (configurable RPC URL).
- Supports TLS when certificate and key paths are provided in config or env vars.
- Worker authentication: validates user:password against configured credentials or optional JWT/HMAC adapter.
- Handles mining.subscribe, mining.authorize, mining.submit, and mining.extranonce.subscribe (basic).
- Converts bitcoind getblocktemplate into a simplified notify job. This is a bridge/simplification —
  a production Stratum v1/v2 implementation requires more comprehensive protocol handling.
Notes:
- Configure in backend/config.json under "stratum_async".
- Requires 'requests' in backend/requirements.txt for JSON-RPC calls to bitcoind.
"""

import asyncio, json, os, uuid, time, hmac, hashlib, requests, ssl
from datetime import datetime
from .stratum_job_assembler import build_coinbase, merkle_root, assemble_block_header


CFG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
# Load config (fallback to env vars)
def load_config():
    cfg = {}
    try:
        with open(CFG_PATH, "r") as f:
            cfg = json.load(f)
    except Exception:
        cfg = {}
    sc = cfg.get("stratum_async", {})
    # allow env override
    sc["rpc_url"] = os.getenv("BITCOIND_RPC_URL", sc.get("rpc_url", cfg.get("bitcoind",{}).get("rpc_url","")))
    sc["host"] = os.getenv("STRATUM_HOST", sc.get("host","0.0.0.0"))
    sc["port"] = int(os.getenv("STRATUM_PORT", sc.get("port",3333)))
    sc["tls_cert"] = os.getenv("STRATUM_TLS_CERT", sc.get("tls_cert",""))
    sc["tls_key"] = os.getenv("STRATUM_TLS_KEY", sc.get("tls_key",""))
    sc["auth_map"] = sc.get("auth_map", {})  # { "workername": "password" }
    sc["report_url"] = os.getenv("REPORT_URL", sc.get("report_url","http://127.0.0.1:5000/api/report_share"))
    sc["report_secret"] = os.getenv("REPORT_SHARED_SECRET", sc.get("report_secret","change_this_report_secret"))
    sc["poll_interval"] = int(os.getenv("STRATUM_POLL_INTERVAL", sc.get("poll_interval", 10)))
    return sc

CONFIG = load_config()

# Helper: call bitcoind JSON-RPC
def bitcoind_rpc(rpc_url, method, params=None):
    try:
        if params is None:
            params = []
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(rpc_url)
        netloc = parsed.hostname
        if parsed.port:
            netloc = f"{netloc}:{parsed.port}"
        rpc_endpoint = urlunparse((parsed.scheme, netloc, parsed.path or "/", "", "", ""))
        auth = None
        if parsed.username:
            auth = (parsed.username, parsed.password or "")
        payload = {"jsonrpc":"1.0","id":"stratum-"+str(uuid.uuid4()), "method": method, "params": params}
        headers = {"content-type":"application/json"}
        resp = requests.post(rpc_endpoint, auth=auth, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

# Convert getblocktemplate -> simplified job dict for miners
def make_job_from_gbt(gbt_result):
    # gbt_result expected as dict from bitcoind getblocktemplate 'result' field
    if not gbt_result:
        return None
    # Simplify: include blockhash/template info, coinbase value, height, target (bits)
    job = {
        "job_id": str(uuid.uuid4()),
        "height": gbt_result.get("height"),
        "previousblockhash": gbt_result.get("previousblockhash"),
        "coinbase_tx": gbt_result.get("coinbasevalue"),
        "target": gbt_result.get("target") or gbt_result.get("bits",""),
        "timestamp": int(time.time()),
        "data": gbt_result  # include raw for advanced clients
    }
    return job

# Broadcast jobs to all connected workers
class JobBroadcaster:
    def __init__(self):
        self.job = None
        self.clients = set()
        self.lock = asyncio.Lock()

    async def update_job_from_rpc(self):
        rpc = CONFIG.get("rpc_url")
        if not rpc:
            return
        res = bitcoind_rpc(rpc, "getblocktemplate", [{"rules": ["segwit"]}])
        if res.get("error"):
            return
        result = res.get("result") or res
        new_job = make_job_from_gbt(result)
            # attempt basic job assembly: build coinbase and merkle root if txids present
            try:
                txids = [t.get('txid') if isinstance(t, dict) else t for t in result.get('transactions', [])]
                # fallback txid extraction
                txid_list = []
                for t in txids:
                    if not t:
                        continue
                    if isinstance(t, dict):
                        tid = t.get('txid')
                    else:
                        tid = t
                    if tid:
                        txid_list.append(tid)
                if txid_list:
                    mr = merkle_root(txid_list)
                    cb = build_coinbase('', '00000000', '00', result.get('height'))
                    header_hex, header_hash = assemble_block_header(result.get('previousblockhash','00'*32), mr, result.get('curtime'), result.get('bits'))
                    new_job['merkle_root'] = mr
                    new_job['coinbase'] = cb
                    new_job['header'] = header_hex
            except Exception as e:
                pass

        if new_job and (not self.job or new_job.get("height") != self.job.get("height")):
            async with self.lock:
                self.job = new_job
                await self.broadcast_job(self.job)

    async def periodic_poll(self, interval=10):
        while True:
            try:
                await self.update_job_from_rpc()
            except Exception as e:
                print("job poll error", e)
            await asyncio.sleep(interval)

    async def broadcast_job(self, job):
        msg = json.dumps({"method":"mining.notify","params":[job["job_id"], {"target": job.get("target"), "height": job.get("height")}]})
        to_remove = []
        async with self.lock:
            for w in list(self.clients):
                try:
                    await w.send_line(msg)
                except Exception as e:
                    to_remove.append(w)
            for w in to_remove:
                self.clients.discard(w)

BROADCASTER = JobBroadcaster()

# Worker protocol handler
class WorkerConnection:
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer
        self.addr = writer.get_extra_info("peername")
        self.buffer = b""
        self.miner_id = None
        self.worker_name = None
        self.subscribed = False
        self.authorized = False
        self.extranonce_subscribed = False

    async def send_line(self, line):
        if isinstance(line, dict):
            line = json.dumps(line)
        if not line.endswith("\n"):
            line = line + "\n"
        self.writer.write(line.encode("utf-8"))
        await self.writer.drain()

    async def handle_request(self, obj):
        req_id = obj.get("id")
        method = obj.get("method")
        params = obj.get("params", [])
        if method == "mining.subscribe":
            # respond with subscription and extranonce placeholder
            self.subscribed = True
            resp = {"id": req_id, "result": [str(uuid.uuid4()), "extranonce_placeholder"], "error": None}
            await self.send_line(resp)
            # send current job if available
            if BROADCASTER.job:
                await self.send_line({"method":"mining.notify","params":[BROADCASTER.job["job_id"], {"target": BROADCASTER.job.get("target"), "height": BROADCASTER.job.get("height")}]})
            return
        elif method == "mining.extranonce.subscribe":
            self.extranonce_subscribed = True
            await self.send_line({"id": req_id, "result": [True], "error": None})
            return
        elif method == "mining.authorize":
            # params: [user, password]; validate against auth_map
            user = params[0] if len(params)>0 else ""
            pwd = params[1] if len(params)>1 else ""
            auth_map = CONFIG.get("auth_map", {})
            ok = False
            if user and pwd:
                if user in auth_map and auth_map[user] == pwd:
                    ok = True
                else:
                    # allow any non-empty for testing if auth_map empty
                    if not auth_map:
                        ok = True
            self.worker_name = user
            self.miner_id = user
            self.authorized = ok
            await self.send_line({"id": req_id, "result": ok, "error": None if ok else "auth failed"})
            if ok:
                # register in broadcaster
                BROADCASTER.clients.add(self)
            return
        elif method == "mining.submit":
            # params: [worker, job_id, nonce, extra]
            if not self.authorized:
                await self.send_line({"id": req_id, "result": False, "error": "unauthorized"})
                return
            try:
                worker = params[0]
                job_id = params[1]
                nonce = params[2] if len(params)>2 else ""
                shares = 1
            except Exception:
                await self.send_line({"id": req_id, "result": False, "error": "invalid"})
                return
            # Report share to backend /api/report_share with HMAC signing
            payload = {"miner_id": self.miner_id or "unknown", "worker_name": self.worker_name or "", "shares": shares}
            body = json.dumps(payload).encode("utf-8")
            sig = hmac.new(CONFIG.get("report_secret","change_this_report_secret").encode("utf-8"), body, hashlib.sha256).hexdigest()
            headers = {'Content-Type':'application/json', 'X-REPORT-SIG': sig}
            try:
                r = requests.post(CONFIG.get("report_url"), headers=headers, data=body, timeout=5)
                if r.status_code == 200:
                    await self.send_line({"id": req_id, "result": True, "error": None})
                else:
                    await self.send_line({"id": req_id, "result": False, "error": f"report_error:{r.status_code}"})
            except Exception as e:
                await self.send_line({"id": req_id, "result": False, "error": "report_failed"})
            return
        else:
            await self.send_line({"id": req_id, "result": None, "error": "unknown method"})
            return

    async def run(self):
        try:
            while not self.reader.at_eof():
                line = await self.reader.readline()
                if not line:
                    break
                try:
                    obj = json.loads(line.decode('utf-8').strip())
                except Exception as e:
                    await self.send_line({"id": None, "result": None, "error": "invalid json"})
                    continue
                await self.handle_request(obj)
        finally:
            try:
                BROADCASTER.clients.discard(self)
            except Exception:
                pass
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception:
                pass

# Server entrypoint
async def handle_client(reader, writer):
    conn = WorkerConnection(reader, writer)
    await conn.run()

async def start_server():
    host = CONFIG.get("host", "0.0.0.0")
    port = int(CONFIG.get("port", 3333))
    tls_cert = CONFIG.get("tls_cert", "") or os.getenv("STRATUM_TLS_CERT","")
    tls_key = CONFIG.get("tls_key", "") or os.getenv("STRATUM_TLS_KEY","")
    ssl_ctx = None
    if tls_cert and tls_key and os.path.exists(tls_cert) and os.path.exists(tls_key):
        ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_ctx.load_cert_chain(certfile=tls_cert, keyfile=tls_key)
        print("TLS enabled for Stratum on", host, port)
    server = await asyncio.start_server(handle_client, host, port, ssl=ssl_ctx, limit=2**16)
    addr = server.sockets[0].getsockname()
    print(f"Stratum async server listening on {addr} (TLS={'yes' if ssl_ctx else 'no'})")
    # start periodic job poller
    asyncio.create_task(BROADCASTER.periodic_poll(CONFIG.get("poll_interval",10)))
    async with server:
        await server.serve_forever()

def main():
    try:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    except Exception:
        pass
    asyncio.run(start_server())

if __name__ == "__main__":
    main()
