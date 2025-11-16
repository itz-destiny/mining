"""
wallet_integration.py - helper functions to integrate with real wallet backends.
This file provides stubs and examples for:
 - simulated (demo)
 - bitcoind JSON-RPC (implemented)
 - BTCPay Server API (example placeholder)

IMPORTANT: These are example functions. Use with caution and secure your RPC credentials.
"""

import requests
import json
import uuid
from urllib.parse import urlparse, urlunparse

def bitcoind_send(rpc_url, to_address, amount_btc):
    """
    Send amount_btc (float) to to_address using bitcoind JSON-RPC sendtoaddress.
    rpc_url should include credentials, e.g. http://rpcuser:rpcpass@127.0.0.1:8332/
    Returns a dict: {"ok": True, "txid": ...} or {"ok": False, "error": "..."}.
    """
    try:
        parsed = urlparse(rpc_url)
        if not parsed.scheme or not parsed.hostname:
            return {"ok": False, "error": "invalid rpc_url"}

        # Build the JSON-RPC endpoint without userinfo (requests will handle auth separately)
        netloc = parsed.hostname
        if parsed.port:
            netloc = f"{netloc}:{parsed.port}"
        rpc_endpoint = urlunparse((parsed.scheme, netloc, parsed.path or "/", "", "", ""))

        # Extract credentials if present
        auth = None
        if parsed.username:
            auth = (parsed.username, parsed.password or "")

        payload = {
            "jsonrpc": "1.0",
            "id": str(uuid.uuid4()),
            "method": "sendtoaddress",
            "params": [to_address, float(amount_btc)]
        }
        headers = {"content-type": "application/json"}
        resp = requests.post(rpc_endpoint, auth=auth, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data and data["error"]:
            return {"ok": False, "error": data["error"]}
        txid = data.get("result")
        return {"ok": True, "txid": txid}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def btcpay_payout(btcpay_host, api_key, to_address, amount):
    # Placeholder for BTCPay payouts
    headers = {"Authorization": f"token {api_key}", "Content-Type":"application/json"}
    data = {"address": to_address, "amount": amount}
    try:
        resp = requests.post(btcpay_host + "/api/v1/payouts", json=data, headers=headers, timeout=10)
        resp.raise_for_status()
        return {"ok": True, "result": resp.json()}
    except Exception as e:
        return {"ok": False, "error": str(e)}
def bitcoind_create_psbt(rpc_url, outputs, fee_rate=None, include_watchonly=False):
    """
    Create an unsigned PSBT via bitcoind 'walletcreatefundedpsbt' RPC.
    - outputs: list of {address: amount}
    Returns {"ok": True, "psbt": "..."} or {"ok": False, "error": "..."}
    """
    try:
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(rpc_url)
        netloc = parsed.hostname
        if parsed.port:
            netloc = f"{netloc}:{parsed.port}"
        rpc_endpoint = urlunparse((parsed.scheme, netloc, parsed.path or "/", "", "", ""))
        auth = None
        if parsed.username:
            auth = (parsed.username, parsed.password or "")

        # prepare RPC params: outputs as dict
        outputs_dict = {}
        for o in outputs:
            outputs_dict.update(o)

        params = [ [outputs_dict], {} ]
        # walletcreatefundedpsbt params: inputs=[], outputs, options, bip32derivs
        payload = {"jsonrpc":"1.0","id":"psbt-"+str(uuid.uuid4()), "method":"walletcreatefundedpsbt", "params": [[], outputs_dict, 0, {"includeWatching": include_watchonly}]}
        headers = {"content-type":"application/json"}
        resp = requests.post(rpc_endpoint, auth=auth, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data.get("error"):
            return {"ok": False, "error": data.get("error")}
        result = data.get("result") or {}
        psbt = result.get("psbt")
        fee = result.get("fee")
        return {"ok": True, "psbt": psbt, "fee": fee}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def bitcoind_finalize_psbt(rpc_url, psbt_base64):
    """
    Finalize a PSBT using bitcoind 'walletprocesspsbt' and optionally 'finalizepsbt' / 'sendrawtransaction'.
    Returns {"ok": True, "hex": "...", "txid": "..."} on success or {"ok": False, "error": "..."}
    """
    try:
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(rpc_url)
        netloc = parsed.hostname
        if parsed.port:
            netloc = f"{netloc}:{parsed.port}"
        rpc_endpoint = urlunparse((parsed.scheme, netloc, parsed.path or "/", "", "", ""))
        auth = None
        if parsed.username:
            auth = (parsed.username, parsed.password or "")

        # walletprocesspsbt
        payload = {"jsonrpc":"1.0","id":"proc-"+str(uuid.uuid4()), "method":"walletprocesspsbt", "params":[psbt_base64, False, "ALL"]}
        headers = {"content-type":"application/json"}
        resp = requests.post(rpc_endpoint, auth=auth, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data.get("error"):
            return {"ok": False, "error": data.get("error")}
        proc_result = data.get("result") or {}
        if proc_result.get("complete"):
            hex_payload = {"jsonrpc":"1.0","id":"final-"+str(uuid.uuid4()), "method":"finalizepsbt", "params":[psbt_base64, False]}
            resp2 = requests.post(rpc_endpoint, auth=auth, json=hex_payload, headers=headers, timeout=30)
            resp2.raise_for_status()
            data2 = resp2.json()
            if data2.get("error"):
                return {"ok": False, "error": data2.get("error")}
            final = data2.get("result") or {}
            hex_tx = final.get("hex")
            # broadcast
            send_payload = {"jsonrpc":"1.0","id":"send-"+str(uuid.uuid4()), "method":"sendrawtransaction", "params":[hex_tx]}
            resp3 = requests.post(rpc_endpoint, auth=auth, json=send_payload, headers=headers, timeout=30)
            resp3.raise_for_status()
            data3 = resp3.json()
            if data3.get("error"):
                return {"ok": False, "error": data3.get("error")}
            txid = data3.get("result")
            return {"ok": True, "hex": hex_tx, "txid": txid}
        else:
            # Not fully signed; return partial result for offline signing
            return {"ok": True, "partial": proc_result, "psbt": psbt_base64}
    except Exception as e:
        return {"ok": False, "error": str(e)}
