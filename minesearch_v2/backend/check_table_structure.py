import sqlite3

conn = sqlite3.connect('/app/minesearch_v2/backend/mines.db')
cursor = conn.cursor()

print("=== SOURCES TABLE STRUCTURE ===")
cursor.execute("PRAGMA table_info(sources)")
for row in cursor.fetchall():
    print(row)

print("\n=== SAMPLE DATA ===")
cursor.execute("SELECT * FROM sources LIMIT 5")
columns = [desc[0] for desc in cursor.description]
print("Columns:", columns)
for row in cursor.fetchall():
    print(row)

conn.close()