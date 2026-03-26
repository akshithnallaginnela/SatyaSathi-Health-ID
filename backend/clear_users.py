import sqlite3

conn = sqlite3.connect('vitalid.db')
cur = conn.cursor()

tables_to_clear = [
    'bp_readings', 'sugar_readings', 'blood_reports', 'health_signals',
    'preventive_care', 'daily_tasks', 'diet_recommendations', 'coin_ledger',
    'audit_logs', 'user_settings', 'reminders', 'reports', 'blockchain_records',
    'user_data_status',
]

for t in tables_to_clear:
    try:
        cur.execute("DELETE FROM " + t)
        print("Cleared: " + t)
    except Exception as e:
        print("Skip " + t + ": " + str(e))

cur.execute("DELETE FROM users")
print("Deleted all users")

conn.commit()
conn.close()
print("Done.")
