import psycopg2
import sys

try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="couchsurfing",
        user="postgres",
        password="postgres",
        options="-c client_encoding=UTF8"
    )
    print("Connected successfully!")
    
    cur = conn.cursor()
    cur.execute("SELECT current_database()")
    db_name = cur.fetchone()[0]
    print(f"Database: {db_name}")
    
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    tables = cur.fetchall()
    print(f"Tables: {len(tables)}")
    for table in tables:
        print(f"  - {table[0]}")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error connecting to PostgreSQL: {e}", file=sys.stderr)
