
#!/usr/bin/env python3
"""
Smoke test: starts a mock bitcoind RPC (serves getblocktemplate), a mock backend /api/report_share,
starts stratum_async pointing to the mock RPC, then runs the example_stratum_client to submit a share.
Runs for ~12 seconds then exits and reports logs.
"""
import http.server, socketserver, threading, json, time, requests, subprocess, os, signal, sys

PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND = os.path.join(PROJ, "backend")
TOOLS = os.path.join(PROJ, "tools")

# 1) Mock bitcoind RPC server
class MockRPCHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('content-length',0))
        body = self.rfile.read(length)
        try:
            req = json.loads(body)
        except:
            req = {}
        method = req.get('method','')
        res = {"result": None, "error": None, "id": req.get('id')}
        if method == "getblocktemplate":
            # return simplified template
            res["result"] = {
                "previousblockhash": "00"*32,
                "transactions": [],
                "coinbasevalue": 625000000,
                "target": "00000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
                "height": 210000,
                "curtime": int(time.time()),
                "bits": 0x1d00ffff
            }
        else:
            res["result"] = None
        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.end_headers()
        self.wfile.write(json.dumps(res).encode())

def start_mock_rpc(port=18332):
    server = socketserver.TCPServer(("127.0.0.1", port), MockRPCHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server

# 2) Mock backend for /api/report_share
from flask import Flask, request, jsonify
app = Flask("mock_backend")
@app.route("/api/report_share", methods=["POST"])
def report_share():
    data = request.get_json() or {}
    print("Mock backend received report:", data)
    return jsonify({"ok": True, "credited": 0.00000001})

def start_mock_backend(port=5001):
    t = threading.Thread(target=lambda: app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False), daemon=True)
    t.start()
    return None

def main():
    print("Starting smoke test...")
    rpc = start_mock_rpc(18332)
    start_mock_backend(5001)
    time.sleep(1)
    # set env vars for stratum_async to point to mock RPC and backend
    env = os.environ.copy()
    env["BITCOIND_RPC_URL"] = "http://rpcuser:rpcpass@127.0.0.1:18332/"
    env["REPORT_URL"] = "http://127.0.0.1:5001/api/report_share"
    env["REPORT_SHARED_SECRET"] = "change_this_report_secret"
    # start stratum_async as a subprocess
    stratum_py = os.path.join(BACKEND, "stratum_async.py")
    print("Starting stratum_async...")
    p = subprocess.Popen([sys.executable, stratum_py], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    time.sleep(2)
    # run example client to submit a share
    client_py = os.path.join(TOOLS, "example_stratum_client.py")
    print("Running example client...")
    c = subprocess.Popen([sys.executable, client_py, "--host", "127.0.0.1", "--port", "3333", "--worker", "testminer"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        out, _ = c.communicate(timeout=6)
        print("Client output:\\n", out.decode())
    except subprocess.TimeoutExpired:
        c.kill()
    # wait a bit and then terminate stratum
    time.sleep(3)
    p.terminate()
    try:
        out, _ = p.communicate(timeout=5)
        print("Stratum output:\\n", out.decode())
    except Exception as e:
        p.kill()
    # shutdown rpc server
    rpc.shutdown()
    print("Smoke test finished. Check above logs for events.")
if __name__ == "__main__":
    main()
