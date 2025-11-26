#!/usr/bin/env python3
"""
example_stratum_client.py - simple TCP client to talk to the minimal Stratum server for testing.
Usage:
  python tools/example_stratum_client.py --url tcp://127.0.0.1:3333 --worker miner1
"""
import socket, json, time, argparse

parser = argparse.ArgumentParser()
parser.add_argument('--host', default='127.0.0.1', help='Stratum host')
parser.add_argument('--port', type=int, default=3333, help='Stratum port')
parser.add_argument('--worker', default='miner1', help='Worker name')
args = parser.parse_args()

def send(sock, obj):
    data = (json.dumps(obj) + "\n").encode('utf-8')
    sock.sendall(data)

with socket.create_connection((args.host, args.port)) as s:
    # subscribe
    send(s, {"id": 1, "method": "mining.subscribe", "params": []})
    time.sleep(0.5)
    # authorize
    send(s, {"id": 2, "method": "mining.authorize", "params": [args.worker, "x"]})
    time.sleep(0.5)
    # submit a fake share
    send(s, {"id": 3, "method": "mining.submit", "params": [args.worker, "jobid", "nonce123"]})
    # read responses
    s.settimeout(2.0)
    try:
        while True:
            line = s.recv(4096)
            if not line:
                break
            print(line.decode('utf-8').strip())
    except Exception as e:
        pass
