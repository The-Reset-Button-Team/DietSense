"""Quick Supabase/PostgreSQL connectivity test — v2 (URL-encoded password)."""
import sys
import os
from urllib.parse import quote_plus

# Load .env manually
env_path = os.path.join(os.path.dirname(__file__), "..", "backend", ".env")
env = {}
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()

supabase_url = env.get("SUPABASE_URL", "")
publishable_key = env.get("SUPABASE_PUBLISHABLE_KEY", "")
secret_key = env.get("SUPABASE_SECRET_KEY", "")
raw_db_url = env.get("SUPABASE_DB_URL", "")

# Fix: URL-encode the password portion if necessary
# Format: postgresql://user:password@host:port/db
# Split at the last @ before the host
def fix_db_url(url: str) -> str:
    """URL-encode special chars in the password of a postgres URL."""
    # Strip scheme
    scheme, rest = url.split("://", 1)
    # Find user:pass vs host — split at the LAST @ before the host
    # user:pass may contain @ which is the problem
    # Format is user:pass@host:port/db
    # Find the host part by finding last @
    at_idx = rest.rfind("@")
    userpass = rest[:at_idx]
    hostdb = rest[at_idx + 1:]
    # Split user and pass
    colon_idx = userpass.index(":")
    user = userpass[:colon_idx]
    password = userpass[colon_idx + 1:]
    encoded_pass = quote_plus(password)
    return f"{scheme}://{user}:{encoded_pass}@{hostdb}"

db_url = fix_db_url(raw_db_url)

print("=" * 60)
print("SUPABASE CONNECTION TEST v2")
print("=" * 60)
print(f"URL       : {supabase_url}")
print(f"DB URL    : {db_url[:70]}...")
print()

# ---- Test 1: Direct PostgreSQL via psycopg2 ----
print("[1] Testing direct PostgreSQL (psycopg2)...")
try:
    import psycopg2
    conn = psycopg2.connect(db_url, connect_timeout=15)
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()[0]
    print(f"    OK - {version[:70]}")

    cur.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public' ORDER BY table_name;"
    )
    tables = [row[0] for row in cur.fetchall()]
    print(f"    Public tables ({len(tables)}): {tables}")
    conn.close()
except Exception as e:
    print(f"    FAIL - {e}")

print()

# ---- Test 2: Supabase REST with publishable key ----
print("[2] Testing REST API with publishable key...")
try:
    import httpx
    resp = httpx.get(
        f"{supabase_url}/rest/v1/",
        headers={
            "apikey": publishable_key,
            "Authorization": f"Bearer {publishable_key}",
        },
        timeout=10,
    )
    print(f"    HTTP {resp.status_code}: {resp.text[:150]}")
except Exception as e:
    print(f"    FAIL - {e}")

print()

# ---- Test 3: Supabase REST with secret key ----
print("[3] Testing REST API with secret key...")
try:
    import httpx
    resp = httpx.get(
        f"{supabase_url}/rest/v1/",
        headers={
            "apikey": secret_key,
            "Authorization": f"Bearer {secret_key}",
        },
        timeout=10,
    )
    print(f"    HTTP {resp.status_code}: {resp.text[:150]}")
except Exception as e:
    print(f"    FAIL - {e}")

print()

# ---- Test 4: Supabase SDK with secret key ----
print("[4] Testing Supabase SDK with secret key...")
try:
    from supabase import create_client
    sb = create_client(supabase_url, secret_key)
    print(f"    OK - client created")
    # Try to list a table that doesn't exist yet — should get 200 or 404, not 401
    resp = httpx.get(
        f"{supabase_url}/rest/v1/foods?limit=1",
        headers={
            "apikey": secret_key,
            "Authorization": f"Bearer {secret_key}",
        },
        timeout=10,
    )
    print(f"    GET /foods?limit=1 => HTTP {resp.status_code}: {resp.text[:100]}")
except Exception as e:
    print(f"    FAIL - {e}")

print()
print("=" * 60)
print("DONE")
