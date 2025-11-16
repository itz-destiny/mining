#!/usr/bin/env python3
"""
worker_simulator.py - simulate a set of miners/workers that post share reports periodically.
Usage:
  python tools/worker_simulator.py --url http://localhost:5000/api/report_share --secret change_this_report_secret --miner miner1 --workers 3 --shares 10 --interval 5
"""
import argparse, time, json, hmac, hashlib, requests, threading, random

parser = argparse.ArgumentParser()
parser.add_argument('--url', required=True)
parser.add_argument('--secret', required=True)
parser.add_argument('--miner', required=True)
parser.add_argument('--workers', type=int, default=1)
parser.add_argument('--shares', type=int, default=10)
parser.add_argument('--interval', type=float, default=10.0)
args = parser.parse_args()

def send_report(miner_id, worker_name):
    body = json.dumps({"miner_id": miner_id, "worker_name": worker_name, "shares": args.shares}).encode('utf-8')
    sig = hmac.new(args.secret.encode('utf-8'), body, hashlib.sha256).hexdigest()
    headers = {'Content-Type':'application/json', 'X-REPORT-SIG': sig}
    try:
        r = requests.post(args.url, headers=headers, data=body, timeout=10)
        print(worker_name, r.status_code, r.text)
    except Exception as e:
        print("error", e)

def worker_loop(miner_id, name):
    while True:
        send_report(miner_id, name)
        time.sleep(args.interval + random.random()*args.interval)

threads = []
for i in range(args.workers):
    name = f"worker{i+1}"
    t = threading.Thread(target=worker_loop, args=(args.miner, name), daemon=True)
    t.start()
    threads.append(t)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("stopping")
