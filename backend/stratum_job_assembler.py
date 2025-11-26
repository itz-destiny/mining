#!/usr/bin/env python3
"""
stratum_job_assembler.py - Build full Stratum-style job templates (simplified) from getblocktemplate.
This module contains helper functions to:
 - build a coinbase transaction with extranonce
 - compute merkle root from txids
 - assemble a simplified block header (little-endian fields handling)
Note: This is a careful approximation for educational/demo use; for production ensure full consensus-valid assembly.
"""
import hashlib, binascii, struct, json, uuid, time

def sha256d(b):
    return hashlib.sha256(hashlib.sha256(b).digest()).digest()

def txid_from_raw(raw_hex):
    raw = binascii.unhexlify(raw_hex)
    return binascii.hexlify(sha256d(raw)[::-1]).decode()  # little-endian txid

def merkle_root(txid_list):
    # txid_list are hex little-endian strings; convert to bytes (big-endian) for hashing
    nodes = [binascii.unhexlify(tx)[::-1] for tx in txid_list]
    if not nodes:
        return None
    while len(nodes) > 1:
        if len(nodes) % 2 == 1:
            nodes.append(nodes[-1])
        new_nodes = []
        for i in range(0, len(nodes), 2):
            new_nodes.append(sha256d(nodes[i] + nodes[i+1]))
        nodes = new_nodes
    # return hex little-endian
    return binascii.hexlify(nodes[0][::-1]).decode()

def build_coinbase(coinbase_script_hex, extranonce1_hex, extranonce2_hex, height):
    """
    Build a simple coinbase transaction hex. This is a minimal coinbase with:
    - version 1
    - 1 input (coinbase) with script = height + extranonces + coinbase_script
    - 1 output paying to no address (placeholder). In production include payout addresses.
    This is a simplified representation and may not be suitable for production.
    """
    # coinbase input script: height (varint) + extranonces + coinbase_script
    height_bytes = bytes([len(str(height))]) + str(height).encode('ascii')
    coinbase_script = coinbase_script_hex or ""
    script = height_bytes + binascii.unhexlify(extranonce1_hex + extranonce2_hex) + binascii.unhexlify(coinbase_script)
    # Build minimal raw tx (not fully compliant for production)
    version = struct.pack("<I", 1)
    in_count = b'\x01'
    prev = b'\x00' * 32 + struct.pack("<I", 0xFFFFFFFF)
    script_len = bytes([len(script)])
    sequence = struct.pack("<I", 0xFFFFFFFF)
    out_count = b'\x01'
    # one dummy output (value 0 sats), script empty
    value = struct.pack("<Q", 0)
    out_script_len = b'\x00'
    locktime = struct.pack("<I", 0)
    raw = version + in_count + prev + script_len + script + sequence + out_count + value + out_script_len + locktime
    return binascii.hexlify(raw).decode()

def assemble_block_header(previousblockhash_hex, merkle_root_hex, ntime=None, nbits=None, nonce=0):
    # previousblockhash_hex is big-endian hex or as returned by bitcoind; convert to little-endian bytes
    prev = binascii.unhexlify(previousblockhash_hex)[::-1]
    merkle = binascii.unhexlify(merkle_root_hex)[::-1]
    version = struct.pack("<I", 536870912)  # example: version with segwit/modern flags
    ntime = struct.pack("<I", int(ntime if ntime is not None else time.time()))
    nbits = struct.pack("<I", int(nbits if nbits is not None else 0x1d00ffff))
    nonce = struct.pack("<I", int(nonce))
    header = version + prev + merkle + ntime + nbits + nonce
    # header hash (double sha256)
    header_hash = binascii.hexlify(sha256d(header)[::-1]).decode()
    return binascii.hexlify(header).decode(), header_hash

if __name__ == "__main__":
    # simple test
    txids = ['00'*32]
    print("merkle:", merkle_root(txids))
