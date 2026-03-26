import sqlite3
conn = sqlite3.connect('vitalid.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print('Tables:', tables)
for t in tables:
    try:
        cur.execute("SELECT COUNT(*) FROM " + t)
        print("  " + t + ": " + str(cur.fetchone()[0]) + " rows")
    except: pass

try:
    cur.execute("SELECT id, full_name, phone_number, health_id FROM users")
    print('\nUsers:')
    for r in cur.fetchall():
        print(' ', r)
except Exception as e:
    print('users error:', str(e))
conn.close()
