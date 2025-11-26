
#!/usr/bin/env bash
set -e
PROJ="/mnt/data/mining_pwa_backend_flask"
cd "$PROJ/backend"
# create venv if missing
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt || true

# export env from .env if present
if [ -f "../.env" ]; then
  export $(grep -v '^#' ../.env | xargs)
fi

# start backend
nohup venv/bin/python server.py > ../backend.log 2>&1 &
echo "Started backend (pid $!)"

# start stratum async
nohup venv/bin/python stratum_async.py > ../stratum.log 2>&1 &
echo "Started stratum_async (pid $!)"
