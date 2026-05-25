import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="couchsurfing",
        user="postgres",
        password="postgres"
    )
    print("Connected successfully!")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
