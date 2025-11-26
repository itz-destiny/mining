
# Example usage for async stratum server:

# Start backend server (ensure backend/server.py is running and accessible):
python backend/server.py

# Start the async stratum server (this will poll bitcoind for jobs and accept miners):
python backend/stratum_async.py

# Connect your miner (cgminer / BFGMiner) to the stratum server address (host:port).
# If you enabled TLS, configure the miner to use TLS and provide the server certificate as needed.
# Worker credentials should be provided as username:password (password checked against config.auth_map).
