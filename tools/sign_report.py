#!/usr/bin/env python3
"""
sign_report.py - helper to HMAC-SHA256 sign a JSON report and POST to server.
Usage:
  python sign_report.py --secret change_this_report_secret --url http://localhost:5000/api/report_share --miner miner123 --worker w1 --shares 100
"""
import argparse, json, hmac, hashlib, requests, sys

parser = argparse.ArgumentParser()
parser.add_argument('--secret', required=True, help='HMAC shared secret')
parser.add_argument('--url', required=True, help='Full URL to /api/report_share endpoint')
parser.add_argument('--miner', required=True, help='Miner ID')
parser.add_argument('--worker', default='', help='Worker name')
parser.add_argument('--shares', type=int, required=True, help='Number of shares to report')
args = parser.parse_args()

body = json.dumps({"miner_id": args.miner, "worker_name": args.worker, "shares": args.shares}).encode('utf-8')
sig = hmac.new(args.secret.encode('utf-8'), body, hashlib.sha256).hexdigest()
headers = {'Content-Type':'application/json', 'X-REPORT-SIG': sig}
resp = requests.post(args.url, headers=headers, data=body)
print('Status:', resp.status_code)
try:
    print(resp.json())
except Exception:
    print(resp.text)
