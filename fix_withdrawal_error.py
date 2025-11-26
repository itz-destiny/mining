#!/usr/bin/env python3
"""
Quick script to fix withdrawal errors by updating error status to completed
or clearing old error withdrawals.
"""
import sqlite3
import os
import sys

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "backend", "data", "withdrawals.db")

def fix_errors():
    """Update all error withdrawals to completed (simulated mode)"""
    if not os.path.exists(DB_PATH):
        print(f"Database not found: {DB_PATH}")
        return
    
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    
    # Get error withdrawals
    cur.execute("SELECT id, amount, currency FROM withdrawals WHERE status='error'")
    errors = cur.fetchall()
    
    if not errors:
        print("✅ No error withdrawals found!")
        return
    
    print(f"Found {len(errors)} error withdrawal(s):")
    for wid, amount, currency in errors:
        print(f"  - {wid[:12]}... : {amount} {currency}")
    
    # Update to completed with simulated txid
    import uuid
    for wid, amount, currency in errors:
        fake_txid = f"sim_tx_{uuid.uuid4()}"
        cur.execute("UPDATE withdrawals SET status=?, txid=? WHERE id=?", 
                   ("completed", fake_txid, wid))
        print(f"✅ Fixed: {wid[:12]}... → completed")
    
    db.commit()
    db.close()
    print(f"\n✅ Fixed {len(errors)} withdrawal(s)!")

def clear_all():
    """Clear all withdrawals (use with caution)"""
    if not os.path.exists(DB_PATH):
        print(f"Database not found: {DB_PATH}")
        return
    
    response = input("⚠️  Delete ALL withdrawals? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute("DELETE FROM withdrawals")
    count = cur.rowcount
    db.commit()
    db.close()
    print(f"✅ Deleted {count} withdrawal(s)")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "clear":
        clear_all()
    else:
        fix_errors()

