import sqlite3
conn = sqlite3.connect('vitalid.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print('Tables:', tables)
for t in tables:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        print(f"  {t}: {cur.fetchone()[0]} rows")
    except: pass

# Show users
try:
    cur.execute("SELECT id, full_name, phone_number, health_id FROM users")
    print('\nUsers:')
    for r in cur.fetchall():
        print(' ', r)
except Exception as e:
    print('users error:', e)
conn.close()
