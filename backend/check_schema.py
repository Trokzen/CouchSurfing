import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="postgres",
    user="postgres",
    password="1234"
)
cur = conn.cursor()
cur.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'couchsurfing';")
result = cur.fetchone()
if result:
    print(f"Schema 'couchsurfing' exists.")
else:
    print("Schema 'couchsurfing' does not exist. Creating...")
    cur.execute("CREATE SCHEMA couchsurfing;")
    conn.commit()
    print("Schema created.")

cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'couchsurfing';")
tables = cur.fetchall()
print(f"Tables in schema couchsurfing: {len(tables)}")
for table in tables:
    print(f"  - {table[0]}")

cur.close()
conn.close()