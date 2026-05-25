import psycopg2

def test_psycopg2():
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='1234',
            database='postgres'
        )
        print("Psycopg2 connected successfully")
        cur = conn.cursor()
        cur.execute("SELECT version()")
        version = cur.fetchone()[0]
        print(f"PostgreSQL version: {version}")
        cur.execute("SELECT current_schema()")
        schema = cur.fetchone()[0]
        print(f"Current schema: {schema}")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Psycopg2 connection error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_psycopg2()