#!/usr/bin/env python3
"""Quick test script to verify the server is running"""
import requests
import time
import sys

def test_server():
    url = "http://localhost:5000/api/status"
    print(f"Testing server at {url}...")
    
    try:
        response = requests.get(url, timeout=5)
        print(f"✓ Server is running!")
        print(f"  Status Code: {response.status_code}")
        print(f"  Response: {response.json()}")
        return True
    except requests.exceptions.ConnectionError:
        print("✗ Server is not running or not accessible")
        print("  Make sure you started it with: python backend/server.py")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    if test_server():
        sys.exit(0)
    else:
        sys.exit(1)


