#!/usr/bin/env python3
"""
stratum_server.py - Minimal educational Stratum-like server (JSON over TCP)
- Accepts TCP connections from miners
- Performs a simplified handshake ("mining.subscribe" / "mining.authorize")
- Issues simple work jobs (simulated) and accepts "mining.submit" as share submissions
- On valid share, it records shares via the /api/report_share HTTP endpoint (HMAC signing required).
Notes:
- This is NOT a production Stratum implementation.
- For real mining pools use battle-tested pool software (node-stratum-pool, poolsoftware), or run as a relay/proxy.
"""

import socket, threading, json, uuid, time, hmac, hashlib, requests, os
from datetime import datetime

HOST = "0.0.0.0"
PORT = int(os.getenv("STRATUM_PORT") or 3333)
REPORT_URL = os.getenv("REPORT_URL") or "http://127.0.0.1:5000/api/report_share"
REPORT_SECRET = os.getenv("REPORT_SHARED_SECRET") or "change_this_report_secret"
PAYOUT_PER_SHARE = float(os.getenv("MINING_PAYOUT_RATE_PER_SHARE") or 1e-10)

# Simple per-connection worker state
class WorkerHandler(threading.Thread):
    def __init__(self, conn, addr):
        super().__init__(daemon=True)
        self.conn = conn
        self.addr = addr
        self.buffer = b""
        self.worker_name = None
        self.miner_id = None
        self.subscribed = False
        self.authorized = False
        self.running = True

    def send_json(self, obj):
        data = (json.dumps(obj) + "\n").encode("utf-8")
        try:
            self.conn.sendall(data)
        except Exception as e:
            print("send error", e)
            self.running = False

    def handle_subscribe(self, req_id, params):
        # respond with a subscription and job_id
        job_id = str(uuid.uuid4())
        self.subscribed = True
        resp = {"id": req_id, "result": [job_id, "mining.set_difficulty"], "error": None}
        self.send_json(resp)
        # issue initial job
        self.issue_job(job_id)

    def handle_authorize(self, req_id, params):
        # params: [user, password]
        if len(params) >= 1:
            self.worker_name = params[0]
            # For simplicity, use worker_name as miner_id
            self.miner_id = self.worker_name
            self.authorized = True
            resp = {"id": req_id, "result": True, "error": None}
            self.send_json(resp)
        else:
            resp = {"id": req_id, "result": False, "error": "missing credentials"}
            self.send_json(resp)

    def issue_job(self, job_id):
        # In a real pool, job contains block header parts, merkle branches, target, etc.
        # Here we create a simulated 'job' containing a random nonce target difficulty
        job = {
            "method": "mining.notify",
            "params": [job_id, {"job_id": job_id, "target": "0000ffff", "data": str(uuid.uuid4())}]
        }
        self.send_json(job)

    def process_submit(self, req_id, params):
        # params: [worker_name, job_id, nonce, extra]
        # Validate basic structure and record share via HTTP report
        if not self.authorized or not self.miner_id:
            resp = {"id": req_id, "result": False, "error": "unauthorized"}
            self.send_json(resp)
            return

        try:
            worker_name = params[0]
            job_id = params[1]
            nonce = params[2] if len(params) > 2 else ""
            shares = 1  # each submit counts as 1 share in this simple demo
        except Exception as e:
            resp = {"id": req_id, "result": False, "error": "invalid submit"}
            self.send_json(resp)
            return

        # Build report payload
        payload = {"miner_id": self.miner_id, "worker_name": worker_name, "shares": shares}
        body = json.dumps(payload).encode('utf-8')
        sig = hmac.new(REPORT_SECRET.encode('utf-8'), body, hashlib.sha256).hexdigest()
        headers = {'Content-Type': 'application/json', 'X-REPORT-SIG': sig}

        try:
            r = requests.post(REPORT_URL, headers=headers, data=body, timeout=5)
            if r.status_code == 200:
                resp = {"id": req_id, "result": True, "error": None}
            else:
                resp = {"id": req_id, "result": False, "error": f"report_error:{r.status_code}"}
        except Exception as e:
            resp = {"id": req_id, "result": False, "error": "report_failed"}

        self.send_json(resp)

    def run(self):
        try:
            while self.running:
                data = self.conn.recv(4096)
                if not data:
                    break
                self.buffer += data
                # Stratum uses newline-delimited JSON-RPC
                while b"\n" in self.buffer:
                    line, self.buffer = self.buffer.split(b"\n", 1)
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line.decode("utf-8"))
                    except Exception as e:
                        print("invalid json", e)
                        continue
                    # handle JSON-RPC with fields: id, method, params
                    req_id = obj.get("id")
                    method = obj.get("method")
                    params = obj.get("params", [])
                    if method == "mining.subscribe":
                        self.handle_subscribe(req_id, params)
                    elif method == "mining.authorize":
                        self.handle_authorize(req_id, params)
                    elif method == "mining.submit":
                        self.process_submit(req_id, params)
                    else:
                        # unknown method - reply with error
                        resp = {"id": req_id, "result": None, "error": "unknown method"}
                        self.send_json(resp)
        finally:
            try:
                self.conn.close()
            except:
                pass
            print("connection closed", self.addr)

def serve():
    print("Starting minimal Stratum server on port", PORT)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(100)
    try:
        while True:
            conn, addr = s.accept()
            print("connection from", addr)
            handler = WorkerHandler(conn, addr)
            handler.start()
    finally:
        s.close()

if __name__ == "__main__":
    serve()
