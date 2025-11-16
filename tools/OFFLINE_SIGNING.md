Offline signing workflow (recommended for mainnet):

1) Run auto_batch_payout.py periodically (cron) to produce unsigned PSBTs for eligible miners.
   Example: python tools/auto_batch_payout.py --server http://localhost:5000 --threshold 0.0001

2) The script calls /api/admin/create_psbt which returns a PSBT base64. Save that to a secure location
   or the script can be extended to automatically fetch and store PSBTs.

3) Transfer the PSBT to an offline signing machine (air-gapped) or hardware wallet interface.
   Use your signers (HWI, hardware wallet, or bitcoin-core on an offline machine with the keys)
   to sign the PSBT. Example using bitcoin-core on an offline machine:
     bitcoin-cli -testnet walletprocesspsbt "<psbt>" false "ALL"
   Or use HWI tools to sign with hardware wallets.

4) Once signed (may be partially signed by multiple cosigners), retrieve the signed PSBT and POST it to:
     POST /api/admin/finalize_psbt
   Body: { "psbt_id": "<id>", "psbt": "<signed_psbt_base64>" }
   This endpoint will attempt to finalize and broadcast the transaction using bitcoind (if configured).

5) Monitor the PSBT status via GET /api/admin/credits or /api/admin/miners or by inspecting the psbts DB table.

Security notes:
- Never expose the PSBTs or private keys over insecure channels.
- Use encrypted transfer methods to move PSBTs between online and offline machines.
- For high-value payouts, use a multi-signature wallet and require multiple cosigners to sign PSBTs.
