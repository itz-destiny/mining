import os
import threading
import time
import sqlite3
import uuid
import json
from flask import Flask, jsonify, request, g, send_from_directory, abort, Response
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
import os as _os
import logging
from ipaddress import ip_network, ip_address
import hmac
import hashlib
import jwt
from passlib.hash import bcrypt
from datetime import datetime, timedelta

from flask_cors import CORS

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "data", "withdrawals.db")
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

# --- Serve frontend static files from /static/... ---
# Try multiple paths: Docker (/frontend), local development (../frontend), or current dir
FRONTEND_DIR = None
possible_paths = [
    "/frontend",  # Docker/Railway path
    os.path.join(os.path.dirname(__file__), "..", "frontend"),  # Local development
    os.path.join(os.path.dirname(__file__), "frontend"),  # Alternative local path
]

for path in possible_paths:
    abs_path = os.path.abspath(path)
    if os.path.exists(abs_path):
        FRONTEND_DIR = abs_path
        break

if FRONTEND_DIR is None:
    # Fallback to first path and let warning show
    FRONTEND_DIR = os.path.abspath(possible_paths[0])

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='/static')

# Production logging configuration
if os.getenv('FLASK_ENV') == 'production':
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s %(levelname)s %(name)s %(message)s',
        handlers=[
            logging.FileHandler('mining_backend.log'),
            logging.StreamHandler()
        ]
    )
else:
    logging.basicConfig(level=logging.INFO)
    
logger = logging.getLogger('mining_backend')

# Make sure FRONTEND_DIR exists
if not os.path.exists(FRONTEND_DIR):
    logger.warning(f"Frontend directory not found: {FRONTEND_DIR}")

# Production error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"ok": False, "error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}")
    return jsonify({"ok": False, "error": "Internal server error"}), 500

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({"ok": False, "error": "Unauthorized"}), 401

@app.after_request
def after_request(response):
    # Security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    if os.getenv('FLASK_ENV') == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Configure CORS more restrictively by default (change via FRONTEND_ORIGIN env)
FRONTEND_ORIGIN = os.getenv('FRONTEND_ORIGIN', 'http://localhost:5000')
CORS(app, origins=[FRONTEND_ORIGIN])

# load environment variables
load_dotenv()

# rate limiter (configurable via env)
use_rl = os.getenv('USE_RATE_LIMIT','true').lower() in ('1','true','yes')
if use_rl:
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=[f"{os.getenv('RATE_LIMIT_PER_MINUTE','60')} per minute"]
    )
else:
    limiter = None

# --- Simple config ---
DEFAULT_CONFIG = {
    "server_api_key": "change_this_server_api_key",
    "mining_rate_per_hash": 0.00000001,  # BTC per hashrate unit per second (simulated)
    "initial_hashrate": 800,
    "wallet_backend": "simulated",  # options: simulated | bitcoind | btcpay
    "bitcoind": {
        "rpc_url": "http://user:pass@127.0.0.1:8332/"
    },
    "btcpay": {
        "host": "https://btcpayserver/",
        "api_key": ""
    }
}

if not os.path.exists(CONFIG_PATH):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(DEFAULT_CONFIG, f, indent=2)

with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

# --- Simple DB setup ---
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)

def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH, check_same_thread=False)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    # Create connection directly (not using get_db() which requires Flask context)
    db = sqlite3.connect(DB_PATH, check_same_thread=False)
    db.row_factory = sqlite3.Row
    cur = db.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS withdrawals (
        id TEXT PRIMARY KEY,
        currency TEXT,
        amount REAL,
        to_address TEXT,
        txid TEXT,
        status TEXT,
        created_at INTEGER
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS miners (
        id TEXT PRIMARY KEY,
        owner TEXT,
        worker_name TEXT,
        balance REAL DEFAULT 0,
        shares INTEGER DEFAULT 0,
        created_at INTEGER
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS credits (
        id TEXT PRIMARY KEY,
        miner_id TEXT,
        shares INTEGER,
        amount REAL,
        created_at INTEGER
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS psbts (
        id TEXT PRIMARY KEY,
        psbt TEXT,
        status TEXT,
        txid TEXT,
        created_at INTEGER
    )
    """)
    db.commit()
    db.close()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

# --- Mining simulation ---
mining_state = {
    "running": False,
    "hashrate": config.get("initial_hashrate", 800),
    "balance": 0.0,
    "last_update": time.time()
}

mining_lock = threading.Lock()

def mining_loop():
    while True:
        time.sleep(1)
        with mining_lock:
            if mining_state["running"]:
                # increment balance based on hashrate
                rate = config.get("mining_rate_per_hash", 1e-8)
                mining_state["balance"] += mining_state["hashrate"] * rate
                mining_state["last_update"] = time.time()

miner_thread = threading.Thread(target=mining_loop, daemon=True)
miner_thread.start()

# --- Wallet integration skeleton ---
# --- Wallet integration helper ---
from wallet_integration import bitcoind_send, btcpay_payout

def send_onchain_payment(currency, amount, address):
    """
    Send on-chain payment. This function supports three modes:
    - simulated: return fake txid
    - bitcoind: use RPC via wallet_integration.bitcoind_send
    - btcpay: use wallet_integration.btcpay_payout (placeholder)
    """
    backend = config.get("wallet_backend", "simulated")
    if backend == "simulated":
        return {"ok": True, "txid": "sim_tx_" + str(uuid.uuid4())}
    elif backend == "bitcoind":
        rpc = config.get("bitcoind", {}).get("rpc_url", "")
        if not rpc:
            return {"ok": False, "error": "bitcoind rpc_url not configured"}
        return bitcoind_send(rpc, address, amount)
    elif backend == "btcpay":
        btcpay_cfg = config.get("btcpay", {})
        return btcpay_payout(btcpay_cfg.get("host",""), btcpay_cfg.get("api_key",""), address, amount)
    else:
        return {"ok": False, "error": "unknown wallet backend"}


# --- API endpoints ---
@app.route("/api/status", methods=["GET"])
def api_status():
    with mining_lock:
        return jsonify({
            "running": mining_state["running"],
            "hashrate": mining_state["hashrate"],
            "balance": round(mining_state["balance"], 8)
        })

@app.route("/api/stream", methods=["GET"])
def api_stream():
    # Server-Sent Events (SSE) streaming endpoint for realtime updates
    def event_stream():
        while True:
            try:
                time.sleep(1)
                with mining_lock:
                    data = {
                        "running": mining_state["running"],
                        "hashrate": mining_state["hashrate"],
                        "balance": round(mining_state["balance"], 8),
                        "ts": int(time.time())
                    }
                yield f"data: {json.dumps(data)}\n\n"
            except GeneratorExit:
                break
            except Exception as e:
                logger.error(f"SSE stream error: {e}")
                break
    
    response = Response(event_stream(), mimetype="text/event-stream")
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    return response

@app.route("/api/start", methods=["POST"])
def api_start():
    with mining_lock:
        mining_state["running"] = True
    return jsonify({"ok": True, "msg": "mining started"})

@app.route("/api/stop", methods=["POST"])
def api_stop():
    with mining_lock:
        mining_state["running"] = False
    return jsonify({"ok": True, "msg": "mining stopped"})

@app.route("/api/set_hashrate", methods=["POST"])
def api_set_hashrate():
    data = request.get_json() or {}
    hr = data.get("hashrate")
    if hr is None:
        return jsonify({"ok": False, "error": "missing hashrate"}), 400
    with mining_lock:
        mining_state["hashrate"] = float(hr)
    return jsonify({"ok": True})

@app.route("/api/withdraw", methods=["POST"])
def api_withdraw():
    data = request.get_json() or {}
    currency = data.get("currency", "BTC")
    amount = float(data.get("amount", 0))
    to_address = data.get("to_address", "")
    if amount <= 0 or not to_address:
        return jsonify({"ok": False, "error": "invalid request"}), 400

    with mining_lock:
        if amount > mining_state["balance"]:
            return jsonify({"ok": False, "error": "insufficient balance"}), 400
        mining_state["balance"] -= amount

    # Create withdrawal record (status 'pending')
    db = get_db()
    cur = db.cursor()
    wid = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO withdrawals (id,currency,amount,to_address,txid,status,created_at) VALUES (?,?,?,?,?,?,?)",
        (wid, currency, amount, to_address, "", "pending", int(time.time()))
    )
    db.commit()

    # Try to process payout immediately (demo: simulated)
    result = send_onchain_payment(currency, amount, to_address)
    cur = db.cursor()
    if result.get("ok"):
        txid = result.get("txid", "")
        cur.execute("UPDATE withdrawals SET status=?, txid=? WHERE id=?", ("completed", txid, wid))
        db.commit()
        return jsonify({"ok": True, "id": wid, "txid": txid})
    else:
        # leave as pending and return id for admin processing
        return jsonify({"ok": True, "id": wid, "note": "pending manual processing"})

# --- Admin endpoints ---

def require_api_key(req=None):
    # Accept either header X-API-KEY or environment variable MINING_SERVER_API_KEY
    provided = None
    if req is not None:
        provided = req.headers.get("X-API-KEY") or req.args.get("api_key")
    env_key = os.getenv("MINING_SERVER_API_KEY") or config.get("server_api_key")
    if not provided or provided != env_key:
        abort(401, "invalid api key")


ADMIN_IP_ALLOWLIST = os.getenv('ADMIN_IP_ALLOWLIST','').split(',')
def admin_protected(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        # optional admin IP allowlist
        remote = request.remote_addr
        if ADMIN_IP_ALLOWLIST and any([ip for ip in ADMIN_IP_ALLOWLIST if ip]):
            allowed = False
            for spec in ADMIN_IP_ALLOWLIST:
                try:
                    if '/' in spec:
                        if ip_address(remote) in ip_network(spec):
                            allowed = True; break
                    else:
                        if remote == spec:
                            allowed = True; break
                except Exception:
                    pass
            if not allowed:
                return jsonify({'ok': False, 'error': 'admin access denied (ip)'}), 403

        # check X-API-KEY header or MINING_SERVER_API_KEY env var
        provided = request.headers.get("X-API-KEY") or request.args.get("api_key")
        env_key = os.getenv("MINING_SERVER_API_KEY") or config.get("server_api_key")
        if not provided or provided != env_key:
            return jsonify({"ok": False, "error": "unauthorized"}), 401
        return f(*args, **kwargs)
    return wrapped


@app.route("/api/report_share", methods=["POST"])
def api_report_share():
    """
    Endpoint for miners or pool servers to report shares earned by a worker.
    Body: { "miner_id": "<id>", "worker_name": "<name>", "shares": <int> }
    This will credit the miner's balance according to MINING_PAYOUT_RATE_PER_SHARE env var or config value.
    Authentication: Requests must include header 'X-REPORT-SIG' which is HMAC-SHA256 of the raw body using REPORT_SHARED_SECRET.
    """
    # Verify HMAC signature to ensure reports are authentic
    shared_secret = os.getenv('REPORT_SHARED_SECRET') or config.get('report_shared_secret') or config.get('stratum_async', {}).get('report_secret') or ''
    sig_header = request.headers.get('X-REPORT-SIG') or request.headers.get('X-SIGNATURE') or ''
    raw = request.get_data() or b''
    if not shared_secret:
        # If no shared secret configured, reject to avoid unauthenticated reports in production by mistake
        return jsonify({"ok": False, "error": "reporting disabled (no secret configured)"}), 403

    # compute expected signature
    try:
        expected = hmac.new(shared_secret.encode('utf-8'), raw, hashlib.sha256).hexdigest()
    except Exception as e:
        return jsonify({"ok": False, "error": "signature computation error"}), 500

    # constant-time compare
    if not sig_header or not hmac.compare_digest(sig_header, expected):
        return jsonify({"ok": False, "error": "invalid signature"}), 401

    # parse JSON body after verifying
    data = request.get_json() or {}
    miner_id = data.get("miner_id")
    worker_name = data.get("worker_name", "")
    try:
        shares = int(data.get("shares", 0) or 0)
    except:
        shares = 0
    if not miner_id or shares <= 0:
        return jsonify({"ok": False, "error": "invalid"}), 400

    payout_per_share = float(os.getenv('MINING_PAYOUT_RATE_PER_SHARE') or config.get('payout_per_share') or 0.0)
    amount = shares * payout_per_share

    db = get_db()
    cur = db.cursor()
    # ensure miner exists
    cur.execute("SELECT * FROM miners WHERE id=?", (miner_id,))
    row = cur.fetchone()
    ts = int(time.time())
    if not row:
        # create miner entry
        cur.execute("INSERT INTO miners (id,owner,worker_name,balance,shares,created_at) VALUES (?,?,?,?,?,?)",
                    (miner_id, "", worker_name, amount, shares, ts))
    else:
        cur.execute("UPDATE miners SET balance = balance + ?, shares = shares + ? WHERE id=?", (amount, shares, miner_id))
    # record credit
    cred_id = str(uuid.uuid4())
    cur.execute("INSERT INTO credits (id, miner_id, shares, amount, created_at) VALUES (?,?,?,?,?)", (cred_id, miner_id, shares, amount, ts))
    db.commit()
    return jsonify({"ok": True, "miner_id": miner_id, "credited": amount, "shares": shares})
@app.route("/api/admin/withdrawals", methods=["GET"])
def api_admin_withdrawals():
    require_api_key(request)
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM withdrawals ORDER BY created_at DESC")
    rows = [dict(r) for r in cur.fetchall()]
    return jsonify({"ok": True, "withdrawals": rows})

@app.route("/api/admin/process", methods=["POST"])
def api_admin_process():
    require_api_key(request)
    data = request.get_json() or {}
    wid = data.get("id")
    action = data.get("action")  # 'approve', 'reject', or 'retry'
    if not wid or action not in ("approve","reject","retry"):
        return jsonify({"ok": False, "error": "invalid"}), 400
    db = get_db()
    cur = db.cursor()
    if action == "approve" or action == "retry":
        # attempt payment when admin approves or retries
        cur.execute("SELECT currency, amount, to_address FROM withdrawals WHERE id=?", (wid,))
        row = cur.fetchone()
        if not row:
            return jsonify({"ok": False, "error": "not found"}), 404
        currency, amount, to_address = row["currency"], row["amount"], row["to_address"]
        result = send_onchain_payment(currency, amount, to_address)
        if result.get("ok"):
            txid = result.get("txid", "")
            cur.execute("UPDATE withdrawals SET status=?, txid=? WHERE id=?", ("completed", txid, wid))
        else:
            # Store error message for debugging
            error_msg = result.get("error", "Payment processing failed")
            logger.error(f"Withdrawal {wid} failed: {error_msg}")
            cur.execute("UPDATE withdrawals SET status=? WHERE id=?", ("error", wid))
    else:
        cur.execute("UPDATE withdrawals SET status=? WHERE id=?", ("rejected", wid))
    db.commit()
    return jsonify({"ok": True})

# --- Serve a simple static status page for testing ---

@app.route("/api/admin/token", methods=["POST"])
def api_admin_token():
    """
    Generate a JWT token for admin authentication.
    Body: { "api_key": "..." }
    Returns: { "ok": True, "token": "..." }
    """
    data = request.get_json() or {}
    provided_key = data.get("api_key") or request.headers.get("X-API-KEY")
    env_key = os.getenv("MINING_SERVER_API_KEY") or config.get("server_api_key")
    
    if not provided_key or provided_key != env_key:
        return jsonify({"ok": False, "error": "invalid api key"}), 401
    
    # Generate JWT token
    jwt_secret = os.getenv("JWT_SECRET") or config.get("server_api_key", "default_secret")
    payload = {
        "sub": "admin",
        "iat": int(time.time()),
        "exp": int(time.time()) + (7 * 24 * 60 * 60)  # 7 days
    }
    token = jwt.encode(payload, jwt_secret, algorithm="HS256")
    return jsonify({"ok": True, "token": token})

@app.route("/api/admin/miners", methods=["GET"])
@admin_protected
def api_admin_miners():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM miners ORDER BY created_at DESC")
    rows = [dict(r) for r in cur.fetchall()]
    return jsonify({"ok": True, "miners": rows})

@app.route("/api/admin/batch_payout", methods=["POST"])
@admin_protected
def api_admin_batch_payout():
    """
    Admin-triggered batch payout.
    Expected body: { "payments": [ { "miner_id": "...", "to_address": "...", "amount": 0.001 }, ... ] }
    For each payment, a withdrawal record is created and send_onchain_payment is attempted immediately.
    Returns list of results per payment.
    """
    data = request.get_json() or {}
    payments = data.get("payments", [])
    if not payments or not isinstance(payments, list):
        return jsonify({"ok": False, "error": "invalid request"}), 400

    results = []
    db = get_db()
    cur = db.cursor()
    for p in payments:
        miner_id = p.get("miner_id")
        to_address = p.get("to_address")
        amount = float(p.get("amount", 0) or 0)
        if not miner_id or not to_address or amount <= 0:
            results.append({"ok": False, "miner_id": miner_id, "error": "invalid payment entry"})
            continue

        # Deduct from miner balance if exist
        cur.execute("SELECT balance FROM miners WHERE id=?", (miner_id,))
        row = cur.fetchone()
        if not row or row["balance"] < amount:
            results.append({"ok": False, "miner_id": miner_id, "error": "insufficient balance or miner not found"})
            continue

        # deduct balance
        cur.execute("UPDATE miners SET balance = balance - ? WHERE id=?", (amount, miner_id))
        # create withdrawal record
        wid = str(uuid.uuid4())
        ts = int(time.time())
        cur.execute("INSERT INTO withdrawals (id,currency,amount,to_address,txid,status,created_at) VALUES (?,?,?,?,?,?,?)",
                    (wid, "BTC", amount, to_address, "", "pending", ts))
        db.commit()

        # attempt payment
        res = send_onchain_payment("BTC", amount, to_address)
        if res.get("ok"):
            txid = res.get("txid","")
            cur.execute("UPDATE withdrawals SET status=?, txid=? WHERE id=?", ("completed", txid, wid))
            db.commit()
            results.append({"ok": True, "miner_id": miner_id, "wid": wid, "txid": txid})
        else:
            results.append({"ok": False, "miner_id": miner_id, "wid": wid, "error": res.get("error")})
    return jsonify({"ok": True, "results": results})


@app.route("/api/admin/psbts", methods=["GET"])
@admin_protected
def api_admin_psbts():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id, status, txid, created_at FROM psbts ORDER BY created_at DESC")
    rows = [dict(r) for r in cur.fetchall()]
    return jsonify({"ok": True, "psbts": rows})

@app.route("/api/admin/get_psbt/<psbt_id>", methods=["GET"])
@admin_protected
def api_admin_get_psbt(psbt_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT psbt, status, txid, created_at FROM psbts WHERE id=?", (psbt_id,))
    row = cur.fetchone()
    if not row:
        return jsonify({"ok": False, "error": "not found"}), 404
    return jsonify({"ok": True, "psbt": row["psbt"], "status": row["status"], "txid": row["txid"], "created_at": row["created_at"]})

@app.route("/api/admin/credits", methods=["GET"])
@admin_protected
def api_admin_credits():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM credits ORDER BY created_at DESC")
    rows = [dict(r) for r in cur.fetchall()]
    return jsonify({"ok": True, "credits": rows})

@app.route("/")
def index():
    # Serve index.html by default
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/index.html")
def frontend_index():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/admin.html")
def frontend_admin():
    return send_from_directory(FRONTEND_DIR, "admin.html")

@app.route("/psbt.html")
def frontend_psbt():
    return send_from_directory(FRONTEND_DIR, "psbt.html")


if __name__ == "__main__":
    # initialize DB
    init_db()
    # optionally allow overriding API key by env var
    env_key = os.environ.get("MINING_SERVER_API_KEY")
    if env_key:
        config["server_api_key"] = env_key
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)
    # Use PORT environment variable (Railway, Heroku, etc.) or default to 5000
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') != 'production'
    print(f"Starting Flask mining backend on http://0.0.0.0:{port}")
    app.run(debug=debug, host="0.0.0.0", port=port)


# --- User auth (JWT) helper functions ---
JWT_SECRET = os.getenv('JWT_SECRET') or config.get('jwt_secret') or 'change_this_jwt_secret'
JWT_ALGO = 'HS256'
JWT_EXP_MINUTES = int(os.getenv('JWT_EXP_MINUTES') or 60*24*7)  # default 1 week

def create_token(user_id):
    exp = datetime.utcnow() + timedelta(minutes=JWT_EXP_MINUTES)
    payload = {"sub": user_id, "exp": exp.timestamp()}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

def verify_token_from_header(req):
    auth = req.headers.get('Authorization') or ''
    if not auth.startswith('Bearer '):
        return None
    token = auth.split(' ',1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return payload.get('sub')
    except Exception:
        return None

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    email = data.get('email','')
    if not username or not password:
        return jsonify({"ok": False, "error": "username and password required"}), 400
    db = get_db()
    cur = db.cursor()
    # check exists
    cur.execute("SELECT id FROM users WHERE username=?", (username,))
    if cur.fetchone():
        return jsonify({"ok": False, "error": "username taken"}), 400
    uid = str(uuid.uuid4())
    ph = bcrypt.hash(password)
    ts = int(time.time())
    cur.execute("INSERT INTO users (id,username,password_hash,email,created_at) VALUES (?,?,?,?,?)", (uid, username, ph, email, ts))
    db.commit()
    token = create_token(uid)
    return jsonify({"ok": True, "user_id": uid, "token": token})

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"ok": False, "error": "username and password required"}), 400
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id, password_hash FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    if not row or not bcrypt.verify(password, row['password_hash']):
        return jsonify({"ok": False, "error": "invalid credentials"}), 401
    token = create_token(row['id'])
    return jsonify({"ok": True, "token": token})

@app.route('/api/user/me', methods=['GET'])
def api_user_me():
    uid = verify_token_from_header(request)
    if not uid:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id, username, email, created_at FROM users WHERE id=?", (uid,))
    row = cur.fetchone()
    if not row:
        return jsonify({"ok": False, "error": "not found"}), 404
    return jsonify({"ok": True, "user": dict(row)})

@app.route('/api/user/link_miner', methods=['POST'])
def api_user_link_miner():
    uid = verify_token_from_header(request)
    if not uid:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    data = request.get_json() or {}
    miner_id = data.get('miner_id')
    if not miner_id:
        return jsonify({"ok": False, "error": "missing miner_id"}), 400
    db = get_db()
    cur = db.cursor()
    # ensure miner exists
    cur.execute("SELECT id FROM miners WHERE id=?", (miner_id,))
    if not cur.fetchone():
        return jsonify({"ok": False, "error": "miner not found"}), 404
    link_id = str(uuid.uuid4())
    ts = int(time.time())
    cur.execute("INSERT INTO user_miners (id,user_id,miner_id,created_at) VALUES (?,?,?,?)", (link_id, uid, miner_id, ts))
    db.commit()
    return jsonify({"ok": True})
