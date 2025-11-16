#!/usr/bin/env python3
"""
auto_batch_payout.py - simple scheduled batch payout helper.
It queries the admin miners endpoint, builds payments for miners with balance >= threshold,
and calls /api/admin/create_psbt to produce an unsigned PSBT which you can sign offline.
Usage:
  export ADMIN_KEY=change_this_server_api_key
  python tools/auto_batch_payout.py --server http://localhost:5000 --threshold 0.0001 --max 50
This script is intended to be run periodically (cron) on a secure host.
"""
import requests, os, time, argparse, math, json

parser = argparse.ArgumentParser()
parser.add_argument('--server', default='http://localhost:5000', help='Backend server URL')
parser.add_argument('--threshold', type=float, default=0.0001, help='Minimum balance to payout')
parser.add_argument('--max', type=int, default=50, help='Max payments per batch')
parser.add_argument('--admin_key', default=os.getenv('ADMIN_KEY') or os.getenv('MINING_SERVER_API_KEY'), help='Admin API key')
args = parser.parse_args()

if not args.admin_key:
    print("Admin key required (env ADMIN_KEY or MINING_SERVER_API_KEY)")
    exit(1)

hdrs = {'X-API-KEY': args.admin_key, 'Content-Type': 'application/json'}

# fetch miners
resp = requests.get(args.server + '/api/admin/miners', headers=hdrs, timeout=20)
if resp.status_code != 200:
    print("Failed to fetch miners:", resp.status_code, resp.text); exit(1)
data = resp.json()
miners = data.get('miners', [])

payments = []
count = 0
for m in miners:
    try:
        bal = float(m.get('balance', 0) or 0)
    except:
        bal = 0.0
    if bal >= args.threshold and count < args.max:
        # create a payment - require admin to have mapping of miner_id -> payout address
        # For demo, we assume miner.owner contains payout address; adapt to your system.
        addr = m.get('owner') or None
        if not addr:
            print("Skipping miner", m.get('id'), "no owner address configured")
            continue
        amt = math.floor(bal * 1e8) / 1e8  # truncate to sat precision approx
        payments.append({'to_address': addr, 'amount': amt})
        count += 1

if not payments:
    print("No payments to process")
    exit(0)

# create PSBT
payload = {'payments': payments}
resp2 = requests.post(args.server + '/api/admin/create_psbt', headers=hdrs, json=payload, timeout=30)
print("Create PSBT status:", resp2.status_code, resp2.text)
